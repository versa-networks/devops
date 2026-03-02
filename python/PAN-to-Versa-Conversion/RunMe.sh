#!/usr/bin/env bash
set -uo pipefail
exec </dev/tty
SCRIPT_SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_DIR="$(pwd -P)"
SCRIPTS_DIR="${MAIN_DIR}/scripts"

FAILED_SCRIPTS=()


run_py() {
  local script_path="$1"
  if [[ ! -f "$script_path" ]]; then
    _box_print "ERROR: Missing script:" "$script_path"
    exit 1
  fi

  echo
  echo "==> Running: ${script_path}"

  local exit_code=0

  (
    cd "$SCRIPTS_DIR" || exit 1
    python3 "$script_path" </dev/tty
  ) || exit_code=$?

  if [[ $exit_code -ne 0 ]]; then
    _box_print "WARNING: Script failed (exit code $exit_code):" "$script_path"
  fi

  return 0
}


_repeat_char() {
  local ch="$1" n="$2"
  printf "%*s" "$n" "" | tr " " "$ch"
}

_box_print() {

  local width="${BOX_WIDTH:-$(tput cols 2>/dev/null || echo 140)}"
  if [[ "$width" -lt 140 ]]; then width=140; fi
  local border="$(_repeat_char "*" "$width")"

  echo "$border"
  for raw in "$@"; do
    raw="${raw//$'\t'/    }"

    local wrap_width=$((width - 4))
   
    while [[ ${#raw} -gt $wrap_width ]]; do
      local chunk="${raw:0:$wrap_width}"
      raw="${raw:$wrap_width}"
      printf "* %-*s *\n" "$wrap_width" "$chunk"
    done
    printf "* %-*s *\n" "$wrap_width" "$raw"
  done
  echo "$border"
}


run_py "${SCRIPTS_DIR}/step-0.py"
run_py "${SCRIPTS_DIR}/step-1.py"
run_py "${SCRIPTS_DIR}/step-2.py"
run_py "${SCRIPTS_DIR}/step-3.py"
run_py "${SCRIPTS_DIR}/step-4.py"
run_py "${SCRIPTS_DIR}/step-5.py"
run_py "${SCRIPTS_DIR}/step-6.py"
run_py "${SCRIPTS_DIR}/step-7.py"
run_py "${SCRIPTS_DIR}/step-8.py"
run_py "${SCRIPTS_DIR}/preconvert-cleanup.py"


messages=()

# 1
if [[ -s "${MAIN_DIR}/must-fix-address-object.txt" ]]; then
  messages+=("There are unresolved address objects that need your intervention. Please open the file "must-fix-address-object.txt", go through the list and fix the address object in either file "../final-data/final-address.txt" or "../final-data/final-address-group.txt"." "" "")
fi

# 2
if [[ -s "${MAIN_DIR}/step-4/step-4_unsupported-service-config.txt" ]]; then
  messages+=("There are unresolved address objects that need your intervention. Please open the file "must-fix-address-object.txt", go through the list and fix the service object in file "../final-data/final-service.txt"." "" "")
fi

# 3
if [[ -s "${MAIN_DIR}/ldap-object-not-found.txt" ]]; then
  messages+=('There are unresolved LDAP users or groups. Some LDAP DN couldn'"'"'t be correlated to the users/group reference file "../ldap-source-input.txt.  Please open the file "../ldap-object-not-found.txt", go through the list and fix the LDAP object reference in file "../final-data/cleaned-pan-rules.txt".')
fi

# 4
if [[ -s "${MAIN_DIR}/zone-conversion.txt" ]]; then
  messages+=("Please make sure you have edited the file "../zone-conversion.txt" to correctly reflect the zones on Versa before polciies conversion." "" "")
fi

# 5
if [[ -s "${MAIN_DIR}/unresolved-objects-configuration.txt" ]]; then
  messages+=("There are unresolved objects being referenced. The specific configuration line has been removed and the affected firewall policies will be converted in DISABLED state." "" "")
fi

# 6 (always)
messages+=('Please remediate the issues displayed above. When you'"'"'re ready, press ENTER. The script will proceed to convert PAN configuration to Versa service template.')
messages+=("You can also press Ctrl-C and manually run these scripts later:" "" "")
messages+=("1-"../scripts/convert-address.py"" "" "")
messages+=("2-"../scripts/convert-group.py"" "" "")
messages+=("3-"../scripts/convert-service.py"" "" "")
messages+=("4-"../scripts/convert-custom-url-profile.py"" "" "")
messages+=("5-"../scripts/convert-security-urlf-profile.py"" "" "")
messages+=("6-"../scripts/convert-policy.py"" "" "")

echo
_box_print "Post-step checks (manual intervention may be required)" "${messages[@]}"
echo
read -r -p "Press ENTER to continue..." _


run_py "${SCRIPTS_DIR}/convert-address.py"
run_py "${SCRIPTS_DIR}/convert-group.py"
run_py "${SCRIPTS_DIR}/convert-service.py"
run_py "${SCRIPTS_DIR}/convert-custom-url-profile.py"
run_py "${SCRIPTS_DIR}/convert-security-urlf-profile.py"
run_py "${SCRIPTS_DIR}/convert-policy.py"
run_py "${SCRIPTS_DIR}/post-conversion.py"
run_py "${SCRIPTS_DIR}/fix-indentation.py"

if [[ -d "${MAIN_DIR}/final-step" ]]; then
  rm -rf "${MAIN_DIR}/final-step"
fi

if [[ -d "${MAIN_DIR}/temp" ]]; then
  rm -rf "${MAIN_DIR}/temp"
fi

if (( ${#FAILED_SCRIPTS[@]} > 0 )); then
  echo
  _box_print "Summary of non-zero exits (review logs/output)" "${FAILED_SCRIPTS[@]}"
fi

echo
_box_print "DONE: Wrapper pipeline completed successfully."
