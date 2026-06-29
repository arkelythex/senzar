#!/usr/bin/env python3
"""
GGA DeepSeek Provider Patch
Installs the DeepSeek API provider into GGA's providers.sh.

Usage:
    python3 scripts/gga-install-deepseek-provider.py

This script modifies the GGA library's providers.sh to add:
  1. execute_deepseek() function — calls DeepSeek Chat API
  2. deepseek case in validate_provider()
  3. deepseek case in execute_provider()
  4. deepseek case in execute_provider_with_timeout()
  5. deepseek case in get_provider_info()
  6. deepseek mention in supported providers list
"""

import sys
import os

CORRECT_PATHS = [
    os.path.expanduser('~/.local/share/gga/lib/providers.sh'),
    '/usr/local/share/gga/lib/providers.sh',
    '/usr/share/gga/lib/providers.sh',
]

CORRECT_PATH = None
for p in CORRECT_PATHS:
    if os.path.exists(p):
        CORRECT_PATH = p
        break

if not CORRECT_PATH:
    # Try to locate via which gga
    import subprocess
    try:
        result = subprocess.run(['which', 'gga'], capture_output=True, text=True, check=True)
        gga_path = result.stdout.strip()
        gga_dir = os.path.dirname(os.path.dirname(gga_path))
        candidate = os.path.join(gga_dir, 'share', 'gga', 'lib', 'providers.sh')
        if os.path.exists(candidate):
            CORRECT_PATH = candidate
    except subprocess.CalledProcessError:
        pass  # gga not in PATH, will fall through to error below
    except Exception as e:
        print(f"Warning: Could not locate GGA via 'which': {e}", file=sys.stderr)

if not CORRECT_PATH:
    print("Error: Could not find GGA providers.sh", file=sys.stderr)
    print("Checked paths:", file=sys.stderr)
    for p in CORRECT_PATHS:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)

print(f"Patching: {CORRECT_PATH}")

with open(CORRECT_PATH, 'r') as f:
    content = f.read()

changes_made = 0

# ---------------------------------------------------------------------------
# 1. Add execute_deepseek function before execute_claude
# ---------------------------------------------------------------------------
fn_target = 'execute_claude() {'
deepseek_fn = '''# ============================================================================
# DeepSeek API Provider
# ============================================================================

execute_deepseek() {
  local model="$1"
  local prompt="$2"
  local api_key="${DEEPSEEK_API_KEY:-}"
  local base_url="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
  local endpoint="$base_url/v1/chat/completions"

  if [[ -z "$api_key" ]]; then
    echo "Error: DEEPSEEK_API_KEY environment variable is not set" >&2
    return 1
  fi

  local json_payload
  if ! json_payload=$(printf '%s' "$prompt" | python3 -c "
import sys, json
prompt = sys.stdin.read()
model = sys.argv[1]
payload = json.dumps({
    'model': model,
    'messages': [
        {'role': 'system', 'content': 'You are a professional code reviewer. Analyze code against the provided coding standards. Be concise, specific, and cite exact lines.'},
        {'role': 'user', 'content': prompt}
    ],
    'temperature': 0.1,
    'max_tokens': 4096
})
print(payload)
" "$model" 2>&1); then
    echo "Error: Failed to build JSON payload" >&2
    return 1
  fi

  local api_response
  api_response=$(curl -sS \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $api_key" \
    -d "$json_payload" \
    "$endpoint" 2>&1)

  local curl_status=$?
  if [[ $curl_status -ne 0 ]]; then
    echo "Error: Failed to connect to DeepSeek API" >&2
    echo "$api_response" >&2
    return 1
  fi

  printf '%s' "$api_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        error = data['error']
        if isinstance(error, dict):
            msg = error.get('message', 'Unknown error')
        else:
            msg = str(error)
        print(f'Error: {msg}', file=sys.stderr)
        sys.exit(1)
    choices = data.get('choices', [])
    if not choices:
        print('Error: Unexpected response format', file=sys.stderr)
        sys.exit(1)
    content = choices[0].get('message', {}).get('content', '')
    if content:
        print(content)
    else:
        print('Error: Empty response', file=sys.stderr)
        sys.exit(1)
except json.JSONDecodeError as e:
    print(f'Error: Invalid JSON response: {e}', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"
  return $?
}

''' + fn_target

if fn_target in content:
    content = content.replace(fn_target, deepseek_fn, 1)
    print('1. Added execute_deepseek function')
    changes_made += 1
else:
    print('1. Could not find execute_claude — skipping')

# ---------------------------------------------------------------------------
# 2. Add to validate_provider
# ---------------------------------------------------------------------------
old_val = '    github)\n      # GitHub Models requires gh CLI for authentication'
if old_val in content:
    new_val = '''    deepseek)
      if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
        echo -e "${RED}? DEEPSEEK_API_KEY not set${NC}"
        echo ""
        echo "Set your DeepSeek API key:"
        echo "  export DEEPSEEK_API_KEY=\"your-key\""
        echo ""
        return 1
      fi
      if ! command -v curl &> /dev/null; then
        echo -e "${RED}? curl not found${NC}"
        echo ""
        return 1
      fi
      if ! command -v python3 &> /dev/null; then
        echo -e "${RED}? python3 not found${NC}"
        echo ""
        return 1
      fi
      local model="${provider#*:}"
      if [[ "$model" == "$provider" || -z "$model" ]]; then
        echo -e "${RED}? DeepSeek requires a model${NC}"
        echo ""
        echo "Specify model in provider config:"
        echo "  PROVIDER=\"deepseek:deepseek-chat\""
        echo ""
        return 1
      fi
      ;;
    github)
      # GitHub Models requires gh CLI for authentication'''
    content = content.replace(old_val, new_val, 1)
    print('2. Added deepseek to validate_provider')
    changes_made += 1
else:
    print('2. Could not find github validate case — skipping')

# ---------------------------------------------------------------------------
# 3. Add to execute_provider
# ---------------------------------------------------------------------------
old_exec = '    github)\n      local model="${provider#*:}"\n      execute_github_models "$model" "$prompt"'
if old_exec in content:
    new_exec = '''    deepseek)
      local model="${provider#*:}"
      execute_deepseek "$model" "$prompt"
      ;;
    github)
      local model="${provider#*:}"
      execute_github_models "$model" "$prompt"'''
    content = content.replace(old_exec, new_exec, 1)
    print('3. Added deepseek to execute_provider')
    changes_made += 1
else:
    print('3. Could not find github execute case — skipping')

# ---------------------------------------------------------------------------
# 4. Add to execute_provider_with_timeout
# ---------------------------------------------------------------------------
old_timeout = '    github)\n      execute_with_timeout "$timeout" "GitHub Models" execute_github_models "$model" "$prompt"'
if old_timeout in content:
    new_timeout = '''    deepseek)
      execute_with_timeout "$timeout" "DeepSeek" execute_deepseek "$model" "$prompt"
      ;;
    github)
      execute_with_timeout "$timeout" "GitHub Models" execute_github_models "$model" "$prompt"'''
    content = content.replace(old_timeout, new_timeout, 1)
    print('4. Added deepseek to execute_provider_with_timeout')
    changes_made += 1
else:
    print('4. No github timeout case found — skipping')

# ---------------------------------------------------------------------------
# 5. Add to get_provider_info
# ---------------------------------------------------------------------------
old_info = '    github)\n      local model="${provider#*:}"\n      echo "GitHub Models (model: $model)"'
if old_info in content:
    new_info = '''    deepseek)
      local model="${provider#*:}"
      echo "DeepSeek (model: $model)"
      ;;
    github)
      local model="${provider#*:}"
      echo "GitHub Models (model: $model)"'''
    content = content.replace(old_info, new_info, 1)
    print('5. Added deepseek to get_provider_info')
    changes_made += 1
else:
    print('5. Could not find github info case — skipping')

# ---------------------------------------------------------------------------
# 6. Update supported providers list
# ---------------------------------------------------------------------------
old_support = '  echo "  - github:<model>"'
if old_support in content:
    new_support = '  echo "  - github:<model>"\n  echo "  - deepseek:<model>"'
    content = content.replace(old_support, new_support, 1)
    print('6. Updated supported providers list')
    changes_made += 1
else:
    print('6. Could not find support list — skipping')

# ---------------------------------------------------------------------------
# Write changes
# ---------------------------------------------------------------------------
if changes_made > 0:
    with open(CORRECT_PATH, 'w') as f:
        f.write(content)
    print(f'\n✓ All {changes_made} changes applied to {CORRECT_PATH}')
else:
    print('\n⚠ No changes were applied — providers.sh may already be patched or in an unexpected format')
    sys.exit(0)
