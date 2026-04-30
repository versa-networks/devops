from __future__ import annotations 

import sys 
import time 
import shutil 
import threading 
from dataclasses import dataclass 
from datetime import datetime 
from pathlib import Path 
from typing import Dict ,List ,Optional 
import re 

SCRIPT_DIR =Path (__file__ ).resolve ().parent 
MAIN_DIR =SCRIPT_DIR .parent 

LOG_DIR =MAIN_DIR /"log"
STEP8_DIR =MAIN_DIR /"step-8"
FINAL_DIR =MAIN_DIR /"final-data"

DEFAULT_USERS_REF =SCRIPT_DIR /"../final-data/final-ldap-users.txt"
DEFAULT_GROUPS_REF =SCRIPT_DIR /"../final-data/final-ldap-groups.txt"

STEP6_CLEANED_RULES =SCRIPT_DIR /"../step-6/step-6_cleaned-pan-rules.txt"
STEP8_CLEANED_RULES =SCRIPT_DIR /"../step-8/step-8_cleaned-pan-rules.txt"

EXTRACTED_USERS_OUT =SCRIPT_DIR /"../step-8/step-8_extracted-ldap-users.txt"
EXTRACTED_GROUPS_OUT =SCRIPT_DIR /"../step-8/step-8_extracted-ldap-groups.txt"

LDAP_OBJECT_NOT_FOUND =MAIN_DIR /"ldap-object-not-found.txt"
LDAP_USERS_NOT_FOUND =MAIN_DIR /"ldap-users-not-found.txt"

FINAL_CLEANED_RULES =SCRIPT_DIR /"../final-data/cleaned-pan-rules.txt"

class _Tee :
    def __init__ (self ,original ,log_fp ):
        self ._original =original 
        self ._log_fp =log_fp 

    def write (self ,s :str )->int :
        n =0 
        try :
            n =self ._original .write (s )
            self ._original .flush ()
        except Exception :
            pass 

        try :
            if getattr (self ._log_fp ,"closed" ,True ):
                return n 
            self ._log_fp .write (s )
            self ._log_fp .flush ()
        except Exception :
            pass 
        return n 

    def flush (self )->None :
        try :
            self ._original .flush ()
        except Exception :
            pass 
        try :
            if not getattr (self ._log_fp ,"closed" ,True ):
                self ._log_fp .flush ()
        except Exception :
            pass 

def _ts ()->str :
    return datetime .now ().strftime ("%Y-%m-%d %H:%M:%S")

def log (msg :str )->None :
    print (f"[{_ts()}] {msg}")

def resolve_user_path (p :str )->Path :
    pp =Path (p )
    if pp .is_absolute ():
        return pp 
    return (SCRIPT_DIR /pp ).resolve ()

FORBIDDEN_USERNAME_CHARS =set ([
"\\","%","*","+","=","?","{","}","|","<",">","(",")",";",":","[","]",'"'
])

def has_forbidden_username_chars (s :str )->bool :
    return any (ch in FORBIDDEN_USERNAME_CHARS for ch in s )

def strip_outer_quotes (s :str )->str :
    ss =s .strip ()
    if len (ss )>=2 and ss [0 ]=='"'and ss [-1 ]=='"':
        return ss [1 :-1 ]
    return ss 

def ensure_quoted_if_space (s :str )->str :
    if " "in s :
        return f"\"{s}\""
    return s 

def is_dn_string (s :str )->bool :

    t =s .strip ()
    return t .lower ().startswith ("cn=")and (",dc="in t .lower ())

def extract_cn_value_from_dn (dn :str )->Optional [str ]:

    s =dn .strip ()
    m =re .search (r"(?i)\bcn=",s )
    if not m :
        return None 
    i =m .end ()
    out =[]
    esc =False 
    while i <len (s ):
        ch =s [i ]
        if esc :
            out .append (ch )
            esc =False 
            i +=1 
            continue 
        if ch =="\\":
            out .append (ch )
            esc =True 
            i +=1 
            continue 
        if ch ==",":
            break 
        out .append (ch )
        i +=1 
    return "".join (out ).strip ()

@dataclass 
class TokenSpan :
    start :int 
    end :int 
    raw :str 
    new :Optional [str ]=None 

    @property 
    def value (self )->str :
        return self .new if self .new is not None else self .raw 

def parse_source_user_tokens (line :str )->List [TokenSpan ]:

    m =re .search (r"\bsource-user\b",line )
    if not m :
        return []

    i =m .end ()
    n =len (line )
    while i <n and line [i ].isspace ():
        i +=1 
    if i >=n :
        return []

    tokens :List [TokenSpan ]=[]

    if line [i ]=="[":
        i +=1 
        in_q =False 
        esc =False 
        j =i 
        while j <n :
            ch =line [j ]
            if esc :
                esc =False 
                j +=1 
                continue 
            if ch =="\\":
                esc =True 
                j +=1 
                continue 
            if ch =='"':
                in_q =not in_q 
                j +=1 
                continue 
            if (not in_q )and ch =="]":
                list_end =j +1 
                break 
            j +=1 
        else :
            return []

        k =i 
        while k <list_end -1 :
            while k <list_end -1 and line [k ].isspace ():
                k +=1 
            if k >=list_end -1 or line [k ]=="]":
                break 

            tok_start =k 
            if line [k ]=='"':
                k +=1 
                esc2 =False 
                while k <list_end -1 :
                    ch2 =line [k ]
                    if esc2 :
                        esc2 =False 
                        k +=1 
                        continue 
                    if ch2 =="\\":
                        esc2 =True 
                        k +=1 
                        continue 
                    if ch2 =='"':
                        k +=1 
                        break 
                    k +=1 
                tok_end =k 
            else :
                if line [k :k +3 ].upper ()=="CN=":
                    while k <list_end -1 and line [k ]!="]"and line [k ]!='"':
                        if line [k ]==" ":
                            look =k +1 
                            while look <list_end -1 and line [look ]==" ":
                                look +=1 
                            if look >=list_end -1 or line [look ]=="]"or line [look ]=='"':
                                break 
                            next_end =look 
                            while next_end <list_end -1 and not line [next_end ].isspace ()and line [next_end ]not in '"]':
                                next_end +=1 
                            if "="not in line [look :next_end ]:
                                break 
                        k +=1 
                    tok_end =k 
                    while tok_end >tok_start and line [tok_end -1 ]==" ":
                        tok_end -=1 
                else :
                    while k <list_end -1 and (not line [k ].isspace ())and line [k ]!="]":
                        k +=1 
                    tok_end =k 

            raw =line [tok_start :tok_end ]
            if raw .strip ():
                tokens .append (TokenSpan (tok_start ,tok_end ,raw ))
        return tokens 

    tok_start =i 
    if line [i ]=='"':
        i +=1 
        esc =False 
        while i <n :
            ch =line [i ]
            if esc :
                esc =False 
                i +=1 
                continue 
            if ch =="\\":
                esc =True 
                i +=1 
                continue 
            if ch =='"':
                i +=1 
                break 
            i +=1 
        tok_end =i 
    else :
        if line [i :i +3 ].upper ()=="CN=":
            while i <n and line [i ]!='"':
                if line [i ]==" ":
                    look =i +1 
                    while look <n and line [look ]==" ":
                        look +=1 
                    if look >=n or line [look ]=='"':
                        break 
                    next_end =look 
                    while next_end <n and not line [next_end ].isspace ()and line [next_end ]!='"':
                        next_end +=1 
                    if "="not in line [look :next_end ]:
                        break 
                i +=1 
            tok_end =i 
            while tok_end >tok_start and line [tok_end -1 ]==" ":
                tok_end -=1 
        else :
            while i <n and not line [i ].isspace ():
                i +=1 
            tok_end =i 

    raw =line [tok_start :tok_end ]
    if raw .strip ():
        tokens .append (TokenSpan (tok_start ,tok_end ,raw ))
    return tokens 

def rebuild_line (line :str ,tokens :List [TokenSpan ])->str :
    if not tokens :
        return line 
    out =[]
    cur =0 
    for t in tokens :
        out .append (line [cur :t .start ])
        out .append (t .value )
        cur =t .end 
    out .append (line [cur :])
    return "".join (out )

def extract_unique_dns_from_file (path :Path )->Dict [str ,str ]:

    dn_map :Dict [str ,str ]={}

    with path .open ("r",encoding ="utf-8",errors ="replace")as f :
        for line in f :
            s =line .strip ()
            if not s :
                continue 

            candidate =strip_outer_quotes (s ).strip ()
            if is_dn_string (candidate ):
                out_tok =s if (s .startswith ('"')and s .endswith ('"'))else ensure_quoted_if_space (candidate )
                k =candidate .casefold ()
                if k not in dn_map :
                    dn_map [k ]=out_tok 
                continue 

            for m in re .finditer (r'"([^"]*)"',s ):
                inner =m .group (1 ).strip ()
                if is_dn_string (inner ):
                    out_tok =ensure_quoted_if_space (inner )
                    k =inner .casefold ()
                    if k not in dn_map :
                        dn_map [k ]=out_tok 

            for m2 in re .finditer (r"(?i)\bcn=",s ):
                start =m2 .start ()
                token_chars =[]
                i =start 
                while i <len (s )and (not s [i ].isspace ()):
                    if s [i ]in ["[","]"]:
                        break 
                    token_chars .append (s [i ])
                    i +=1 
                tok ="".join (token_chars ).strip ().strip ('"')
                if is_dn_string (tok ):
                    out_tok =ensure_quoted_if_space (tok )
                    k =tok .casefold ()
                    if k not in dn_map :
                        dn_map [k ]=out_tok 

    return dn_map 

def write_extracted_file (out_path :Path ,dn_map :Dict [str ,str ])->None :
    out_path .parent .mkdir (parents =True ,exist_ok =True )
    with out_path .open ("w",encoding ="utf-8",errors ="replace")as f :
        for k in sorted (dn_map .keys ()):
            f .write (dn_map [k ].rstrip ("\n")+"\n")

def build_dn_index (users_dn_map :Dict [str ,str ],groups_dn_map :Dict [str ,str ])->Dict [str ,str ]:

    combined :Dict [str ,str ]={}
    for k ,v in groups_dn_map .items ():
        combined [k ]=v 
    for k ,v in users_dn_map .items ():
        if k not in combined :
            combined [k ]=v 
    return combined 

def build_cn_index (users_dn_map :Dict [str ,str ],groups_dn_map :Dict [str ,str ])->Dict [str ,str ]:

    cn_index :Dict [str ,str ]={}

    def add_from (dn_map :Dict [str ,str ],label :str )->None :
        for tok in dn_map .values ():
            dn =strip_outer_quotes (tok ).strip ()
            cn =extract_cn_value_from_dn (dn )
            if cn is None :
                continue 
            k =cn .casefold ()
            if k not in cn_index :
                cn_index [k ]=tok 
            else :
                if cn_index [k ]!=tok :
                    log (f"WARNING: duplicate CN key '{cn}' while indexing {label}. Keeping first occurrence.")

    add_from (groups_dn_map ,"groups")
    add_from (users_dn_map ,"users")
    return cn_index 

def reset_not_found_files ()->None :
    if LDAP_OBJECT_NOT_FOUND .exists ():
        LDAP_OBJECT_NOT_FOUND .unlink ()
    if LDAP_USERS_NOT_FOUND .exists ():
        LDAP_USERS_NOT_FOUND .unlink ()

UNRESOLVED_HEADER = (
    "\u2554" + "\u2550" * 87 + "\u2557\n"
    "\u2551  " + "!!  ATTENTION  !!".center(85) + "  \u2551\n"
    "\u2560" + "\u2550" * 87 + "\u2563\n"
    "\u2551  The LDAP users and groups listed below could not be resolved during             \u2551\n"
    "\u2551  processing. They are referenced in your source firewall configuration but       \u2551\n"
    "\u2551  could not be matched against the LDAP reference data provided. Firewall         \u2551\n"
    "\u2551  policies referring to these objects have been set to DISABLED status in the     \u2551\n"
    "\u2551  output configuration file. Please remediate and manually enable the affected    \u2551\n"
    "\u2551  policies.                                                                       \u2551\n"
    "\u255a" + "\u2550" * 87 + "\u255d\n"
    "\n"
)

def append_not_found (path :Path ,config_line :str ,value :str )->None :
    if not path .exists ():
        with path .open ("w",encoding ="utf-8",errors ="replace")as f :
            f .write (UNRESOLVED_HEADER )
    with path .open ("a",encoding ="utf-8",errors ="replace")as f :
        f .write (config_line .rstrip ("\n")+"\n")
        f .write (f"{value} >> not found\n")

def is_ad_user_token (raw_token :str )->bool :

    t =strip_outer_quotes (raw_token ).strip ()
    if not t :
        return False 
    if t .lower ().startswith ("cn="):
        return False 
    if ","in t :
        return False 
    return ("\\"in t )or ("@"in t )

def extract_username_from_ad_token (raw_token :str )->Optional [str ]:

    t =strip_outer_quotes (raw_token ).strip ()
    if "@"in t :
        return t .split ("@",1 )[0 ].strip ()
    if "\\"in t :
        parts =re .split (r"\\+",t )
        return parts [-1 ].strip ()
    return None 

def is_canonical_token (raw_token :str )->bool :

    t =strip_outer_quotes (raw_token ).strip ()
    if not t or t .lower ().startswith ("cn="):
        return False 
    if "/"not in t :
        return False 
    first =t .split ("/",1 )[0 ]
    return "."in first 

def extract_username_from_canonical (raw_token :str )->Optional [str ]:
    t =strip_outer_quotes (raw_token ).strip ()
    if "/"not in t :
        return None 
    return t .rsplit ("/",1 )[-1 ].strip ()

def is_slash_login_token (raw_token :str )->bool :

    t =strip_outer_quotes (raw_token ).strip ()
    if not t or t .lower ().startswith ("cn=")or ","in t :
        return False 
    if "/"not in t :
        return False 
    first =t .split ("/",1 )[0 ]
    return "."not in first and len (first )>0 

def extract_username_from_slash_login (raw_token :str )->Optional [str ]:
    t =strip_outer_quotes (raw_token ).strip ()
    if "/"not in t :
        return None 
    return t .rsplit ("/",1 )[-1 ].strip ()

def wait_enter_or_timeout (seconds :int )->None :
    try :
        import select 
        r ,_w ,_e =select .select ([sys .stdin ],[],[],seconds )
        if r :
            try :
                sys .stdin .readline ()
            except Exception :
                pass 
    except Exception :
        time .sleep (seconds )

def read_line_with_timeout (seconds :int )->str :
    try :
        import select 
        r ,_w ,_e =select .select ([sys .stdin ],[],[],seconds )
        if r :
            return sys .stdin .readline ()
        return ""
    except Exception :
        time .sleep (seconds )
        return ""

@dataclass 
class Counters :
    lines_with_source_user :int =0 
    dn_casefixed :int =0 
    dn_not_found :int =0 
    ad_replaced :int =0 
    ad_not_found :int =0 
    canonical_replaced :int =0 
    canonical_not_found :int =0 
    slash_replaced :int =0 
    slash_not_found :int =0 
    invalid_usernames :int =0 
    lines_modified :int =0 

def extract_policy_name_from_line (line :str )->Optional [str ]:
    m =re .search (r"security\s+rules\s+",line )
    if not m :
        return None 
    rest =line [m .end ():]
    if rest .startswith ('"'): 
        eq =rest .find ('"',1 )
        if eq ==-1 :
            return None 
        return rest [1 :eq ]
    sp =rest .find (' ')
    if sp ==-1 :
        return rest .strip ()
    return rest [:sp ]

def set_disabled_yes_for_policies (out_lines :List [str ],disabled_policies :set )->List [str ]:
    if not disabled_policies :
        return out_lines 
    result =list (out_lines )
    for policy_name in disabled_policies :
        if ' 'in policy_name :
            quoted =f'"{re.escape(policy_name)}"'
        else :
            quoted =f'(?:"{re.escape(policy_name)}"|{re.escape(policy_name)})'
        policy_pat =re .compile (r"security\s+rules\s+"+quoted +r"(?:\s|$)")
        policy_indices =[i for i ,l in enumerate (result )if policy_pat .search (l )]
        if not policy_indices :
            continue 
        disabled_idx =None 
        for idx in policy_indices :
            if re .search (r"\bdisabled\b",result [idx ]):
                disabled_idx =idx 
                break 
        if disabled_idx is not None :
            result [disabled_idx ]=re .sub (r"\bdisabled\s+no\b","disabled yes",result [disabled_idx ])
            log (f"Disabled policy (LDAP unresolved): {policy_name} -- set disabled yes")
        else :
            first_line =result [policy_indices [0 ]]
            m2 =policy_pat .search (first_line )
            if m2 :
                prefix =first_line [:m2 .end ()].rstrip ()
                new_line =prefix +" disabled yes\n"
                result .insert (policy_indices [-1 ]+1 ,new_line )
                log (f"Disabled policy (LDAP unresolved): {policy_name} -- inserted disabled yes")
    return result 

def process_rules_file (rules_path :Path ,dn_index :Dict [str ,str ],cn_index :Dict [str ,str ])->Counters :
    counters =Counters ()
    disabled_policies :set =set ()

    out_lines :List [str ]=[]
    with rules_path .open ("r",encoding ="utf-8",errors ="replace")as f :
        for line in f :
            if "source-user"not in line :
                out_lines .append (line )
                continue 

            tokens =parse_source_user_tokens (line )
            if not tokens :
                out_lines .append (line )
                continue 

            counters .lines_with_source_user +=1 
            modified =False 

            for t in tokens :
                dn_content =strip_outer_quotes (t .value ).strip ()
                if not is_dn_string (dn_content ):
                    continue 

                k =dn_content .casefold ()
                if k in dn_index :
                    ref_tok =dn_index [k ]
                    ref_dn =strip_outer_quotes (ref_tok ).strip ()

                    if dn_content !=ref_dn :
                        t .new =ref_tok 
                        modified =True 
                        counters .dn_casefixed +=1 
                        log (f"Step4: case-fix DN: {dn_content}  -->  {ref_tok}")
                else :
                    cn_val =extract_cn_value_from_dn (dn_content )
                    if cn_val is not None :
                        uk =cn_val .casefold ()
                        if uk in cn_index :
                            ref_tok =cn_index [uk ]
                            t .new =ref_tok 
                            modified =True 
                            counters .dn_casefixed +=1 
                            log (f"Step4: CN-fallback match: {dn_content}  -->  {ref_tok}")
                        else :
                            counters .dn_not_found +=1 
                            policy_name =extract_policy_name_from_line (line )
                            if policy_name :
                                disabled_policies .add (policy_name )
                            append_not_found (LDAP_OBJECT_NOT_FOUND ,line ,t .value .strip ())
                            log (f"Step4: DN NOT FOUND (no CN match) -> {t.value.strip()}")
                    else :
                        counters .dn_not_found +=1 
                        policy_name =extract_policy_name_from_line (line )
                        if policy_name :
                            disabled_policies .add (policy_name )
                        append_not_found (LDAP_OBJECT_NOT_FOUND ,line ,t .value .strip ())
                        log (f"Step4: DN NOT FOUND -> {t.value.strip()}")

            for t in tokens :
                cur =t .value 
                if is_dn_string (strip_outer_quotes (cur ).strip ()):
                    continue 
                if not is_ad_user_token (cur ):
                    continue 

                username =extract_username_from_ad_token (cur )
                if username is None :
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,strip_outer_quotes (cur ).strip ())
                    log (f"Step5: INVALID AD token -> {cur.strip()}")
                    continue 

                if has_forbidden_username_chars (username ):
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,username )
                    log (f"Step5: INVALID username (forbidden chars) -> {username}")
                    continue 

                uk =username .casefold ()
                if uk in cn_index :
                    ref_tok =cn_index [uk ]
                    t .new =ref_tok 
                    modified =True 
                    counters .ad_replaced +=1 
                    log (f"Step5: replaced '{cur.strip()}' with '{ref_tok}' (CN match='{username}')")
                else :
                    counters .ad_not_found +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,username )
                    log (f"Step5: username NOT FOUND -> {username}")

            for t in tokens :
                cur =t .value 
                if is_dn_string (strip_outer_quotes (cur ).strip ()):
                    continue 
                if not is_canonical_token (cur ):
                    continue 

                username =extract_username_from_canonical (cur )
                if username is None :
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_OBJECT_NOT_FOUND ,line ,strip_outer_quotes (cur ).strip ())
                    log (f"Step6: INVALID canonical token -> {cur.strip()}")
                    continue 

                if has_forbidden_username_chars (username ):
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_OBJECT_NOT_FOUND ,line ,username )
                    log (f"Step6: INVALID canonical username (forbidden chars) -> {username}")
                    continue 

                uk =username .casefold ()
                if uk in cn_index :
                    ref_tok =cn_index [uk ]
                    t .new =ref_tok 
                    modified =True 
                    counters .canonical_replaced +=1 
                    log (f"Step6: replaced '{cur.strip()}' with '{ref_tok}' (CN match='{username}')")
                else :
                    counters .canonical_not_found +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_OBJECT_NOT_FOUND ,line ,username )
                    log (f"Step6: canonical username NOT FOUND -> {username}")

            for t in tokens :
                cur =t .value 
                if is_dn_string (strip_outer_quotes (cur ).strip ()):
                    continue 
                if is_canonical_token (cur ):
                    continue 
                if not is_slash_login_token (cur ):
                    continue 

                username =extract_username_from_slash_login (cur )
                if username is None :
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,strip_outer_quotes (cur ).strip ())
                    log (f"SlashLogin: INVALID token -> {cur.strip()}")
                    continue 

                if has_forbidden_username_chars (username ):
                    counters .invalid_usernames +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,username )
                    log (f"SlashLogin: INVALID username (forbidden chars) -> {username}")
                    continue 

                uk =username .casefold ()
                if uk in cn_index :
                    ref_tok =cn_index [uk ]
                    t .new =ref_tok 
                    modified =True 
                    counters .slash_replaced +=1 
                    log (f"SlashLogin: replaced '{cur.strip()}' with '{ref_tok}' (CN match='{username}')")
                else :
                    counters .slash_not_found +=1 
                    policy_name =extract_policy_name_from_line (line )
                    if policy_name :
                        disabled_policies .add (policy_name )
                    append_not_found (LDAP_USERS_NOT_FOUND ,line ,username )
                    log (f"SlashLogin: username NOT FOUND -> {username}")

            if modified :
                counters .lines_modified +=1 
                line =rebuild_line (line ,tokens )

            out_lines .append (line )

    out_lines =set_disabled_yes_for_policies (out_lines ,disabled_policies )

    with rules_path .open ("w",encoding ="utf-8",errors ="replace")as f2 :
        f2 .writelines (out_lines )

    return counters 

def main ()->int :
    LOG_DIR .mkdir (parents =True ,exist_ok =True )
    STEP8_DIR .mkdir (parents =True ,exist_ok =True )

    log_path =LOG_DIR /"step-8.log"
    with log_path .open ("a",encoding ="utf-8",errors ="replace")as log_fp :
        sys .stdout =_Tee (sys .__stdout__ ,log_fp )
        sys .stderr =_Tee (sys .__stderr__ ,log_fp )

        log ("========== Step-8 LDAP cleanup: START ==========")

        log (f'Enter "LDAP users reference file" (Press Enter for default: {DEFAULT_USERS_REF})')
        u_in =read_line_with_timeout (15 ).strip ()
        users_ref =resolve_user_path (u_in )if u_in else DEFAULT_USERS_REF .resolve ()

        log (f'Enter "LDAP groups reference file" (Press Enter for default: {DEFAULT_GROUPS_REF})')
        g_in =read_line_with_timeout (15 ).strip ()
        groups_ref =resolve_user_path (g_in )if g_in else DEFAULT_GROUPS_REF .resolve ()

        log (f"Users reference : {users_ref}")
        log (f"Groups reference: {groups_ref}")

        if (not users_ref .exists ())or (not groups_ref .exists ()):
            msg =(
            "LDAP objects reference file doesn't exist. This is crucial in validating and sanitizing groups objects in "
            "firewall policies. Unless you're certain the firewall policies don't use LDAP groups."
            )
            log (msg )
            log ("Exiting.")
            sys .stdout =sys .__stdout__ 
            sys .stderr =sys .__stderr__ 
            return 1 

        log ("Step2: extracting unique LDAP DNs from users+groups reference files...")
        users_dn_map =extract_unique_dns_from_file (users_ref )
        groups_dn_map =extract_unique_dns_from_file (groups_ref )

        write_extracted_file (EXTRACTED_USERS_OUT ,users_dn_map )
        write_extracted_file (EXTRACTED_GROUPS_OUT ,groups_dn_map )

        log (f"Wrote: {EXTRACTED_USERS_OUT} (count={len(users_dn_map)})")
        log (f"Wrote: {EXTRACTED_GROUPS_OUT} (count={len(groups_dn_map)})")

        dn_index =build_dn_index (users_dn_map ,groups_dn_map )
        cn_index =build_cn_index (users_dn_map ,groups_dn_map )

        log (f"DN index size={len(dn_index)}")
        log (f"CN index size={len(cn_index)}")

        if STEP6_CLEANED_RULES .exists ():
            STEP8_CLEANED_RULES .parent .mkdir (parents =True ,exist_ok =True )
            shutil .copy2 (STEP6_CLEANED_RULES ,STEP8_CLEANED_RULES )
            log (f"Copied rules: {STEP6_CLEANED_RULES} -> {STEP8_CLEANED_RULES}")
        else :
            log (f"WARNING: {STEP6_CLEANED_RULES} not found. Continuing...")

        if not STEP8_CLEANED_RULES .exists ():
            log (f"ERROR: {STEP8_CLEANED_RULES} not found. Exiting.")
            sys .stdout =sys .__stdout__ 
            sys .stderr =sys .__stderr__ 
            return 1 

        reset_not_found_files ()

        counters =process_rules_file (STEP8_CLEANED_RULES ,dn_index ,cn_index )

        log ("Processing summary:")
        log (f"  lines_with_source_user : {counters.lines_with_source_user}")
        log (f"  dn_casefixed           : {counters.dn_casefixed}")
        log (f"  dn_not_found           : {counters.dn_not_found}")
        log (f"  ad_replaced            : {counters.ad_replaced}")
        log (f"  ad_not_found           : {counters.ad_not_found}")
        log (f"  canonical_replaced     : {counters.canonical_replaced}")
        log (f"  canonical_not_found    : {counters.canonical_not_found}")
        log (f"  slash_replaced         : {counters.slash_replaced}")
        log (f"  slash_not_found        : {counters.slash_not_found}")
        log (f"  invalid_usernames      : {counters.invalid_usernames}")
        log (f"  lines_modified         : {counters.lines_modified}")

        FINAL_DIR .mkdir (parents =True ,exist_ok =True )
        shutil .copy2 (STEP8_CLEANED_RULES ,FINAL_CLEANED_RULES )
        log (f"Copied final rules: {STEP8_CLEANED_RULES} -> {FINAL_CLEANED_RULES}")

        if LDAP_OBJECT_NOT_FOUND .exists ()and LDAP_OBJECT_NOT_FOUND .stat ().st_size >0 :
            warn_msg =(
            "****************************************************************************************************************"
            "WARNING: There are LDAP objects from source policies that could not be matched to actual LDAP objects list. "
            "You should review and manually rectify the discrepancies in the final firewall policies BEFORE import into VOS. "
            "It will FAIL if the LDAP object in the policies don't exist."
            "****************************************************************************************************************"
            )
            log (warn_msg )
            log ("Press Enter to continue (auto-continue in 30 seconds)...")
            wait_enter_or_timeout (30 )

        log ("========== Step-8 LDAP cleanup: END ==========")
        sys .stdout =sys .__stdout__ 
        sys .stderr =sys .__stderr__ 
        return 0 

if __name__ =="__main__":
    raise SystemExit (main ())