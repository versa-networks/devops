#!/bin/bash

exec </dev/tty

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_DIR="$SCRIPT_DIR/scripts"
TEMP_DIR="$SCRIPT_DIR/temp"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PRE_SCRIPTS=(
    "get-token.py"
    "step-0.py"
    "step-1.py"
    "step-2.py"
    "step-3.py"
    "step-4.py"
    "step-5.py"
    "step-6.py"
    "step-7.py"
    "step-8.py"
    "preconvert-cleanup.py"
)

POST_SCRIPTS=(
    "convert-address.py"
    "convert-address-group.py"
    "convert-service.py"
    "convert-url-category.py"
    "get-url-category-uuid.py"
    "convert-security-urlf-profile.py"
    "convert-policy.py"
)

ALL_SCRIPTS=("${PRE_SCRIPTS[@]}" "${POST_SCRIPTS[@]}")
TOTAL=${#ALL_SCRIPTS[@]}
PASSED=0
FAILED=0
STEP=0

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo -e "${CYAN}${BOLD}        Concerto Migration Pipeline${NC}"
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo ""
}

print_summary() {
    echo ""
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo -e "${CYAN}${BOLD}                  Summary${NC}"
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo -e "  Total  : ${BOLD}${TOTAL}${NC}"
    echo -e "  Passed : ${GREEN}${BOLD}${PASSED}${NC}"
    echo -e "  Failed : ${RED}${BOLD}${FAILED}${NC}"
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo ""
}

box_print() {
    local width=120
    local border
    border="$(printf '%*s' "$width" '' | tr ' ' '*')"
    local inner_width=$((width - 4))
    echo ""
    echo -e "${YELLOW}${BOLD}${border}${NC}"
    for raw in "$@"; do
        raw="${raw//$'\t'/    }"
        while [[ ${#raw} -gt $inner_width ]]; do
            local chunk="${raw:0:$inner_width}"
            raw="${raw:$inner_width}"
            printf "${YELLOW}${BOLD}* %-*s *${NC}\n" "$inner_width" "$chunk"
        done
        printf "${YELLOW}${BOLD}* %-*s *${NC}\n" "$inner_width" "$raw"
    done
    echo -e "${YELLOW}${BOLD}${border}${NC}"
    echo ""
}

run_py() {
    local name="$1"
    local full_path="$PY_DIR/$name"
    STEP=$((STEP + 1))

    echo -e "${BOLD}[${STEP}/${TOTAL}]${NC} Running ${YELLOW}${name}${NC} ..."

    if [[ ! -f "$full_path" ]]; then
        echo -e "        ${RED}MISSING${NC} - file not found: ${full_path}"
        FAILED=$((FAILED + 1))
        echo ""
        return 1
    fi

    python3 "$full_path"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo -e "        ${GREEN}OK${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "        ${RED}FAILED${NC} (exit code: ${exit_code})"
        FAILED=$((FAILED + 1))
        echo ""
        print_summary
        exit 1
    fi

    echo ""
}

print_banner

run_py "get-token.py"

SCIM_SCRIPT="$PY_DIR/get-concerto-scim.py"
GENERAL_FILE="$TEMP_DIR/general.txt"

if [[ -f "$GENERAL_FILE" ]] && grep -q "^scim-profile >>" "$GENERAL_FILE"; then
    if [[ -f "$SCIM_SCRIPT" ]]; then
        STEP=$((STEP + 1))
        echo -e "${BOLD}[${STEP}/${TOTAL}]${NC} Running ${YELLOW}get-concerto-scim.py${NC} ..."
        python3 "$SCIM_SCRIPT"
        SCIM_EXIT=$?
        if [[ $SCIM_EXIT -eq 0 ]]; then
            echo -e "        ${GREEN}OK${NC}"
            PASSED=$((PASSED + 1))
        else
            echo -e "        ${RED}FAILED${NC} (exit code: ${SCIM_EXIT})"
            FAILED=$((FAILED + 1))
            echo ""
            print_summary
            exit 1
        fi
        echo ""
    else
        echo -e "        ${YELLOW}SCIM script:${NC} scim-profile found but get-concerto-scim.py not found in temp/"
        echo ""
    fi
fi

LDAP_USERS_FILE="$TEMP_DIR/concerto-ldap-users.txt"
LDAP_GROUPS_FILE="$TEMP_DIR/ldap-groups-uuid.txt"
LDAP_MERGED_FILE="$SCRIPT_DIR/ldap-source-input.txt"

if [[ -f "$LDAP_MERGED_FILE" ]]; then
    echo -e "        ${GREEN}LDAP merge:${NC} ldap-source-input.txt already exists, skipping merge"
    echo ""
elif [[ -f "$LDAP_USERS_FILE" && -f "$LDAP_GROUPS_FILE" ]]; then
    {
        echo "----BEGIN USERS----"
        cat "$LDAP_USERS_FILE"
        echo ""
        echo "----END USERS----"
        echo ""
        echo "----BEGIN GROUPS----"
        echo ""
        cat "$LDAP_GROUPS_FILE"
        echo ""
        echo "----END GROUPS----"
    } > "$LDAP_MERGED_FILE"
    echo -e "        ${GREEN}LDAP merge:${NC} ldap-source-input.txt created from concerto-ldap-users.txt + ldap-groups-uuid.txt"
    echo ""
else
    echo -e "        ${YELLOW}LDAP merge:${NC} skipped - one or both source files not found in temp/"
    echo ""
fi

for name in "${PRE_SCRIPTS[@]}"; do
    [[ "$name" == "get-token.py" ]] && continue

    if [[ "$name" == "step-7.py" || "$name" == "step-8.py" ]]; then
        if ! grep -q "^ldap-profile >>" "$GENERAL_FILE" 2>/dev/null; then
            STEP=$((STEP + 1))
            echo -e "${BOLD}[${STEP}/${TOTAL}]${NC} Skipping ${YELLOW}${name}${NC} - no ldap-profile in general.txt"
            if [[ "$name" == "step-7.py" ]]; then
                SRC_RULES="$SCRIPT_DIR/step-6/step-6_cleaned-pan-rules.txt"
                DST_RULES="$SCRIPT_DIR/final-data/cleaned-pan-rules.txt"
                if [[ -f "$SRC_RULES" ]]; then
                    mkdir -p "$SCRIPT_DIR/final-data"
                    cp "$SRC_RULES" "$DST_RULES"
                    echo -e "        ${GREEN}Copied:${NC} step-6/step-6_cleaned-pan-rules.txt -> final-data/cleaned-pan-rules.txt"
                else
                    echo -e "        ${RED}Missing:${NC} step-6/step-6_cleaned-pan-rules.txt not found, skipping copy"
                fi
            fi
            echo ""
            continue
        fi
    fi

    run_py "$name"
done

messages=()

if [[ -s "$SCRIPT_DIR/must-fix-address-object.txt" ]]; then
    messages+=(
        "There are unresolved address objects that need your intervention."
        "Please open 'must-fix-address-object.txt', go through the list and fix the address"
        "object in either 'final-data/final-address.txt' or 'final-data/final-address-group.txt'."
        ""
    )
fi

if [[ -s "$SCRIPT_DIR/step-4/step-4_unsupported-service-config.txt" ]]; then
    messages+=(
        "There are unsupported service configurations that need your intervention."
        "Please open 'step-4/step-4_unsupported-service-config.txt', go through the list and fix"
        "the service object in file 'final-data/final-service.txt'."
        ""
    )
fi

if [[ -s "$SCRIPT_DIR/ldap-object-not-found.txt" ]]; then
    messages+=(
        "There are unresolved LDAP users or groups."
        "Some LDAP DNs couldn't be correlated to the users/group reference file 'ldap-source-input.txt'."
        "Please open 'ldap-object-not-found.txt', go through the list and fix the LDAP object"
        "reference in file 'final-data/cleaned-pan-rules.txt'."
        ""
    )
fi

if [[ -s "$SCRIPT_DIR/zone-conversion.txt" ]]; then
    messages+=(
        "Please make sure you have edited 'zone-conversion.txt' to correctly reflect"
        "the zones on Versa before policies conversion."
        ""
    )
fi

if [[ -s "$SCRIPT_DIR/unresolved-objects-configuration.txt" ]]; then
    messages+=(
        "There are unresolved objects being referenced."
        "The specific configuration lines have been removed and the affected firewall policies"
        "will be converted in DISABLED state."
        ""
    )
fi

messages+=(
    "Please remediate any issues displayed above. When you're ready, press ENTER."
    "The script will proceed to convert the configuration to Versa Concerto."
    ""
    "You can also press Ctrl-C and manually run these scripts later:"
    "  1 - scripts/convert-address.py"
    "  2 - scripts/convert-address-group.py"
    "  3 - scripts/convert-service.py"
    "  4 - scripts/convert-url-category.py"
    "  5 - scripts/get-url-category-uuid.py"
    "  6 - scripts/convert-security-urlf-profile.py"
    "  7 - scripts/convert-policy.py"
)

box_print "Post-step checks (manual intervention may be required)" "${messages[@]}"

read -r -p "Press ENTER to continue..." _
echo ""

for name in "${POST_SCRIPTS[@]}"; do
    run_py "$name"
done

GENERAL="$SCRIPT_DIR/temp/general.txt"
FINAL_RULES="$SCRIPT_DIR/final-data/cleaned-pan-rules.txt"
NEED_COPY=false

if [[ -f "$GENERAL" ]]; then
    HAS_LDAP=$(grep -c "^ldap-profile >>" "$GENERAL" 2>/dev/null || echo 0)
    HAS_SCIM=$(grep -c "^scim-profile >>" "$GENERAL" 2>/dev/null || echo 0)
    if [[ "$HAS_LDAP" -eq 0 || "$HAS_SCIM" -eq 0 ]]; then
        NEED_COPY=true
    fi
else
    NEED_COPY=true
fi

if [[ ! -f "$FINAL_RULES" ]]; then
    NEED_COPY=true
fi

if [[ "$NEED_COPY" == true ]]; then
    FALLBACKS=(
        "$SCRIPT_DIR/step-8/step-8_cleaned-pan-rules.txt"
        "$SCRIPT_DIR/step-7/step-7_cleaned-pan-rules.txt"
        "$SCRIPT_DIR/step-6/step-6_cleaned-pan-rules.txt"
    )
    COPIED=false
    for SRC in "${FALLBACKS[@]}"; do
        if [[ -f "$SRC" ]]; then
            mkdir -p "$SCRIPT_DIR/final-data"
            cp "$SRC" "$FINAL_RULES"
            echo -e "${BOLD}Fallback:${NC} ${GREEN}copied $(basename "$SRC") -> final-data/cleaned-pan-rules.txt${NC}"
            COPIED=true
            break
        fi
    done
    if [[ "$COPIED" == false ]]; then
        echo -e "${BOLD}Fallback:${NC} ${RED}no source found for cleaned-pan-rules.txt${NC}"
    fi
fi

#if [[ -d "$TEMP_DIR" ]]; then
#    rm -rf "$TEMP_DIR"
#    echo -e "${BOLD}Cleanup:${NC} ${GREEN}temp/ deleted${NC}"
#else
#    echo -e "${BOLD}Cleanup:${NC} ${YELLOW}temp/ not found, skipping${NC}"
#fi

print_summary

POLICY_RESULTS_FILE="$SCRIPT_DIR/post-policy-results.txt"

if [[ -f "$POLICY_RESULTS_FILE" ]]; then
    POLICY_SUCCESS=0
    POLICY_FAILED=0
    POLICY_FAILED_LINES=()

    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" ]] && continue
        if [[ "$line" =~ [[:space:]]*\>\>[[:space:]]*201([[:space:]].*)?$ ]]; then
            POLICY_SUCCESS=$((POLICY_SUCCESS + 1))
        else
            POLICY_FAILED=$((POLICY_FAILED + 1))
            POLICY_FAILED_LINES+=("$line")
        fi
    done < "$POLICY_RESULTS_FILE"

    POLICY_TOTAL=$((POLICY_SUCCESS + POLICY_FAILED))

    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo -e "${CYAN}${BOLD}           Policy Push Results${NC}"
    echo -e "${CYAN}${BOLD}=================================================${NC}"
    echo -e "  Total    : ${BOLD}${POLICY_TOTAL}${NC}"
    echo -e "  Success  : ${GREEN}${BOLD}${POLICY_SUCCESS}${NC}"
    echo -e "  Failed   : ${RED}${BOLD}${POLICY_FAILED}${NC}"
    echo -e "${CYAN}${BOLD}=================================================${NC}"

    if [[ ${#POLICY_FAILED_LINES[@]} -gt 0 ]]; then
        echo ""
        echo -e "${RED}${BOLD}Policies that did not return 201:${NC}"
        for entry in "${POLICY_FAILED_LINES[@]}"; do
            echo -e "  ${RED}${entry}${NC}"
        done
    fi
    echo ""
else
    echo -e "${YELLOW}${BOLD}Policy results file not found: ${POLICY_RESULTS_FILE}${NC}"
    echo ""
fi

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}Pipeline completed successfully.${NC}"
else
    echo -e "${RED}${BOLD}Pipeline completed with errors.${NC}"
fi
echo ""