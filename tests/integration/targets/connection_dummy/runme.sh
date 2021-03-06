#!/usr/bin/env bash

[[ -n "$DEBUG" || -n "$ANSIBLE_DEBUG" ]] && set -x

set -euo pipefail

cleanup() {
    echo "Cleanup"
}

trap cleanup INT TERM EXIT

cat > test_connection.inventory << EOF
[dummy]
dummy-no-pipelining ansible_pipelining=false
dummy-pipelining    ansible_pipelining=true

[dummy:vars]
ansible_connection=felixfontein.playground.dummy
EOF

echo "Run tests"

# Cannot use the standard connection tests, since this plugin doesn't do anything!
# ./runme-connection.sh "$@"

ansible-playbook -i test_connection.inventory test.yml "$@"

if ansible --version | grep ansible | grep -E ' 2\.(9|10|11|12|13)\.'; then
    LC_ALL=C LANG=C ansible-playbook -i test_connection.inventory test.yml "$@"
fi
