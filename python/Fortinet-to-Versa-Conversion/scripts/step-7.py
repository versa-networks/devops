


from __future__ import annotations 

import re 
import sys 
import shutil 
from pathlib import Path 
from datetime import datetime 

def input_with_timeout(prompt: str, timeout_sec: int = 15, default: str = "") -> str:
    import select
    sys.stdout.write(prompt)
    sys.stdout.flush()
    rlist, _, _ = select.select([sys.stdin], [], [], timeout_sec)
    if rlist:
        return sys.stdin.readline().rstrip("\n")
    sys.stdout.write("\n")
    sys.stdout.flush()
    return default


class Tee :
    def __init__ (self ,*streams ):
        self .streams =streams 

    def write (self ,data ):
        for s in self .streams :
            try :
                s .write (data )
                s .flush ()
            except Exception :
                pass 

    def flush (self ):
        for s in self .streams :
            try :
                s .flush ()
            except Exception :
                pass 

def ts ()->str :
    return datetime .now ().strftime ("%Y-%m-%d %H:%M:%S")

def resolve_from_scripts_dir (scripts_dir :Path ,user_path :str )->Path :
    p =Path (user_path ).expanduser ()
    if p .is_absolute ():
        return p 
    return (scripts_dir /p ).resolve ()

def ensure_dirs (main_dir :Path )->tuple [Path ,Path ,Path ]:
    log_dir =main_dir /"log"
    step_dir =main_dir /"step-7"
    final_dir =main_dir /"final-data"
    log_dir .mkdir (parents =True ,exist_ok =True )
    step_dir .mkdir (parents =True ,exist_ok =True )

    final_dir .mkdir (parents =True ,exist_ok =True )
    return log_dir ,step_dir ,final_dir 

KEY_RE =re .compile (r"(CN|cn|OU|ou|DC|dc)\s*=\s*",flags =0 )

def parse_value_generic (text :str ,i :int )->tuple [str ,int ,bool ]:

    buf =[]
    escaped =False 

    while i <len (text ):
        ch =text [i ]

        if escaped :
            buf .append (ch )
            escaped =False 
            i +=1 
            continue 

        if ch =="\\":
            buf .append (ch )
            escaped =True 
            i +=1 
            continue 

        if ch in "\r\n\t":
            break 
        if ch =='"':
            break 
        if ch in ")]}>":
            break 

        if ch ==" "and (i +1 )<len (text )and text [i +1 ]==" ":
            break 

        if ch ==",":
            value ="".join (buf ).rstrip ()
            return value ,i ,True 

        buf .append (ch )
        i +=1 

    value ="".join (buf ).rstrip ()
    return value ,i ,False 

def parse_value_dc_ldh_comma_only (text :str ,i :int )->tuple [str ,int ,bool ]:

    buf =[]

    while i <len (text ):
        ch =text [i ]
        if ("A"<=ch <="Z")or ("a"<=ch <="z")or ("0"<=ch <="9")or (ch =="-"):
            buf .append (ch )
            i +=1 
        else :
            break 

    value ="".join (buf )
    if not value :
        return "",i ,False 

    j =i 
    while j <len (text )and text [j ]==" ":
        j +=1 

    if j <len (text )and text [j ]==",":
        return value ,j ,True 

    return value ,i ,False 

def parse_dn_at (text :str ,start_idx :int )->tuple [str |None ,int ]:

    i =start_idx 

    m =KEY_RE .match (text ,i )
    if not m or m .group (1 )not in ("CN","cn"):
        return None ,start_idx +1 

    parts :list [str ]=[]
    key =m .group (1 )
    i =m .end ()

    val ,i ,ended_by_comma =parse_value_generic (text ,i )
    if not val .strip ():
        return None ,start_idx +1 
    parts .append (f"{key}={val.strip()}")

    while True :

        while i <len (text )and text [i ]==" ":
            i +=1 
        if i >=len (text ):
            break 

        if ended_by_comma :
            if text [i ]!=",":
                break 
            i +=1 
        else :
            break 

        while i <len (text )and text [i ]==" ":
            i +=1 

        m2 =KEY_RE .match (text ,i )
        if not m2 :
            break 

        key2 =m2 .group (1 )
        i =m2 .end ()

        if key2 in ("DC","dc"):
            val2 ,i ,ended_by_comma =parse_value_dc_ldh_comma_only (text ,i )
        else :
            val2 ,i ,ended_by_comma =parse_value_generic (text ,i )

        if not val2 .strip ():
            break 

        parts .append (f"{key2}={val2.strip()}")

    dn =",".join (parts )
    return dn ,i 

def standardize_dn_separators (dn :str )->str :

    dn =re .sub (r"\s*,\s*",",",dn )
    dn =re .sub (r"\b(CN|cn|OU|ou|DC|dc)\s*=\s*",lambda m :f"{m.group(1)}=",dn )
    return dn .strip ()

def is_valid_dn (dn :str )->bool :

    if not (dn .startswith ("CN=")or dn .startswith ("cn=")):
        return False 
    dcs =re .findall (r"(?:^|,)(?:DC|dc)=[^,]+",dn )
    return len (dcs )>=2 

def wrap_if_space (s :str )->str :
    return f"\"{s}\""if any (ch .isspace ()for ch in s )else s 

def extract_block (text :str ,begin_marker :str ,end_marker :str )->str :

    b =text .find (begin_marker )
    if b <0 :
        return ""
    b_end =b +len (begin_marker )
    e =text .find (end_marker ,b_end )
    if e <0 :
        return ""
    return text [b_end :e ]

def extract_unique_dns_from_block (block_text :str )->list [str ]:

    start_pat =re .compile (r"\b(CN|cn)\s*=",flags =0 )

    seen :set [str ]=set ()
    out :list [str ]=[]

    for m in start_pat .finditer (block_text ):
        dn_raw ,_end =parse_dn_at (block_text ,m .start ())
        if dn_raw is None :
            continue 

        dn =standardize_dn_separators (dn_raw )

        if not is_valid_dn (dn ):
            continue 

        if dn not in seen :
            seen .add (dn )
            out .append (dn )

    return out 

def write_list (path :Path ,items :list [str ])->None :
    path .parent .mkdir (parents =True ,exist_ok =True )
    with open (path ,"w",encoding ="utf-8")as f :
        for item in items :
            f .write (wrap_if_space (item )+"\n")

def main ()->int :
    script_path =Path (__file__ ).resolve ()
    scripts_dir =script_path .parent 
    main_dir =scripts_dir .parent 

    log_dir ,step_dir ,final_dir =ensure_dirs (main_dir )
    log_file =log_dir /"step-7.log"

    with open (log_file ,"a",encoding ="utf-8")as lf :
        sys .stdout =Tee (sys .__stdout__ ,lf )
        sys .stderr =Tee (sys .__stderr__ ,lf )

        print (f"\n[{ts()}] ===== Step-7 LDAP extraction START =====")
        print (f"[{ts()}] script_path: {script_path}")
        print (f"[{ts()}] scripts_dir: {scripts_dir}")
        print (f"[{ts()}] main_dir   : {main_dir}")
        print (f"[{ts()}] log_file   : {log_file}")
        print (f"[{ts()}] step_dir   : {step_dir}")
        print (f"[{ts()}] final_dir  : {final_dir}")

        default_ref ="../ldap-source-input.txt"
        try :
            user_in = input_with_timeout(f'Enter LDAP users and groups reference file [{default_ref}]: ', 15, '').strip()
        except (EOFError ,KeyboardInterrupt ):
            print (f"\n[{ts()}] Input cancelled by user.")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (cancelled) =====\n")
            return 1 

        ref_path_str =user_in if user_in else default_ref 
        ref_path =resolve_from_scripts_dir (scripts_dir ,ref_path_str )

        print (f"[{ts()}] Reference file (raw)     : {ref_path_str}")
        print (f"[{ts()}] Reference file (resolved): {ref_path}")

        if not ref_path .exists ()or not ref_path .is_file ():
            print (
            "LDAP objects reference file doesn't exist. This is crucial in validating and sanitizing users and groups objects in firewall policies. Unless you're certain the firewall policies don't use LDAP users and groups."
            )
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (missing input file) =====\n")
            return 1 

        try :
            text =ref_path .read_text (encoding ="utf-8",errors ="replace")
        except Exception as e :
            print (f"[{ts()}] ERROR: Failed to read reference file: {e}")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (read error) =====\n")
            return 1 

        print (f"[{ts()}] Input length (chars): {len(text)}")

        users_begin ="----BEGIN USERS----"
        users_end ="----END USERS----"
        users_block =extract_block (text ,users_begin ,users_end )
        if not users_block :
            print (f"[{ts()}] WARNING: Users markers not found or empty block: '{users_begin}' .. '{users_end}'")
        users_dns =extract_unique_dns_from_block (users_block )
        print (f"[{ts()}] USERS: unique DNs extracted: {len(users_dns)}")

        users_out =step_dir /"step-7_extracted-users.txt"
        try :
            write_list (users_out ,users_dns )
        except Exception as e :
            print (f"[{ts()}] ERROR: Failed to write users file: {e}")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (users write error) =====\n")
            return 1 
        print (f"[{ts()}] USERS file written: {users_out}")

        users_final =final_dir /"final-ldap-users.txt"
        try :
            shutil .copyfile (users_out ,users_final )
        except Exception as e :
            print (f"[{ts()}] ERROR: Failed to copy users file to final-data: {e}")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (users copy error) =====\n")
            return 1 
        print (f"[{ts()}] USERS file copied to: {users_final}")

        groups_begin ="----BEGIN GROUPS----"
        groups_end ="----END GROUPS----"
        groups_block =extract_block (text ,groups_begin ,groups_end )
        if not groups_block :
            print (f"[{ts()}] WARNING: Groups markers not found or empty block: '{groups_begin}' .. '{groups_end}'")
        groups_dns =extract_unique_dns_from_block (groups_block )
        print (f"[{ts()}] GROUPS: unique DNs extracted: {len(groups_dns)}")

        groups_out =step_dir /"step-7_extracted-groups.txt"
        try :
            write_list (groups_out ,groups_dns )
        except Exception as e :
            print (f"[{ts()}] ERROR: Failed to write groups file: {e}")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (groups write error) =====\n")
            return 1 
        print (f"[{ts()}] GROUPS file written: {groups_out}")

        groups_final =final_dir /"final-ldap-groups.txt"
        try :
            shutil .copyfile (groups_out ,groups_final )
        except Exception as e :
            print (f"[{ts()}] ERROR: Failed to copy groups file to final-data: {e}")
            print (f"[{ts()}] ===== Step-7 LDAP extraction END (groups copy error) =====\n")
            return 1 
        print (f"[{ts()}] GROUPS file copied to: {groups_final}")

        print (f"[{ts()}] ===== Step-7 LDAP extraction END (success) =====\n")
        return 0 

if __name__ =="__main__":
    raise SystemExit (main ())
