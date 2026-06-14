#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${SAT20_DOCS_REPO_URL:-${STP_DOCS_REPO_URL:-https://github.com/sat20-labs/docs}}"
BRANCH="${SAT20_DOCS_BRANCH:-${STP_DOCS_BRANCH:-main}}"
SKILL_NAME="${SAT20_SKILL_NAME:-${STP_SKILL_NAME:-sat20-agent-wallet}}"
SKILL_PATH="ai/sat20-agent-wallet/skills/${SKILL_NAME}"

if [[ -n "${SAT20_SKILLS_DIR:-}" ]]; then
  SKILLS_DIR="${SAT20_SKILLS_DIR}"
elif [[ -n "${STP_SKILLS_DIR:-}" ]]; then
  SKILLS_DIR="${STP_SKILLS_DIR}"
elif [[ -n "${AGENT_SKILLS_DIR:-}" ]]; then
  SKILLS_DIR="${AGENT_SKILLS_DIR}"
elif [[ -n "${CODEX_HOME:-}" ]]; then
  SKILLS_DIR="${CODEX_HOME}/skills"
else
  SKILLS_DIR="${HOME}/.codex/skills"
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

archive_url="${REPO_URL}/archive/refs/heads/${BRANCH}.tar.gz"
archive_path="${tmp_dir}/docs.tar.gz"

echo "Downloading SAT20 Agent Wallet skill from ${archive_url}"
curl -fsSL "${archive_url}" -o "${archive_path}"
tar -xzf "${archive_path}" -C "${tmp_dir}"

repo_root="$(find "${tmp_dir}" -maxdepth 1 -type d -name "docs-*" | head -n 1)"
source_dir="${repo_root}/${SKILL_PATH}"

if [[ ! -f "${source_dir}/SKILL.md" ]]; then
  echo "Cannot find ${SKILL_PATH}/SKILL.md in ${archive_url}" >&2
  exit 1
fi

mkdir -p "${SKILLS_DIR}"
target_dir="${SKILLS_DIR}/${SKILL_NAME}"

if [[ -e "${target_dir}" ]]; then
  backup_dir="${target_dir}.backup.$(date +%Y%m%d%H%M%S)"
  echo "Existing skill found. Moving it to ${backup_dir}"
  mv "${target_dir}" "${backup_dir}"
fi

cp -R "${source_dir}" "${target_dir}"

echo "Installed ${SKILL_NAME} to ${target_dir}"
echo "For Codex, invoke it as: \$${SKILL_NAME}"
echo "Set SAT20_ADAPTER_URL or SAT20_CLIENT_CMD before value-moving operations."
