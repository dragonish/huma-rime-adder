#!/bin/bash

echo "版本迭代脚本"

version_file=data/version.py

# 获取当前版本并去除可能的 'v' 前缀
get_current_version() {
  ver=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
  ver=${ver:-"0.0.0"}
  echo "$ver"
}

current=$(get_current_version)

# 分割版本号
IFS='.' read -r -a version_parts <<< "$current"
major="${version_parts[0]}"
minor="${version_parts[1]}"
patch="${version_parts[2]}"

# 初始化标志
has_breaking_change=false
has_feature_change=false
has_patch_change=false

# 获取提交记录
commits=$(git log --pretty=format:"%s %b" $(git describe --tags --abbrev=0 HEAD)..HEAD)

echo "检查提交记录："
echo "$commits"
echo "----------------------------------"

# 分析每个提交
while IFS= read -r commit; do
    # 检查是否包含 BREAKING CHANGE 脚注
    if echo "$commit" | grep -q "BREAKING CHANGE:"; then
        has_breaking_change=true
    fi
    # 检查是否是 feat 或 deprecate 开头的提交
    if echo "$commit" | grep -qE '^(feat|deprecate):' || echo "$commit" | grep -qE '^(feat|deprecate)\([^)]*\):'; then
        has_feature_change=true
    fi
    
    # 如果既不是破坏性变更也不是功能变更，则视为 patch 变更
    if [[ "$has_breaking_change" == false && "$has_feature_change" == false ]]; then
        # 确保至少有一个提交
        if [[ -n "$commit" ]]; then
            has_patch_change=true
        fi
    fi
done <<< "$commits"

# 确定版本号更新类型
if [[ "$has_breaking_change" == true ]]; then
    # MAJOR 版本更新 - 有破坏性变更
    echo "✓ 发现破坏性变更"
    new_version="$((major + 1)).0.0"
    update_type="MAJOR"
elif [[ "$has_feature_change" == true ]]; then
    # MINOR 版本更新 - 有功能/废弃变更
    echo "✓ 发现功能/废弃提交"
    new_version="$major.$((minor + 1)).0"
    update_type="MINOR"
else
    # PATCH 版本更新 - 其他情况
    new_version="$major.$minor.$((patch + 1))"
    update_type="PATCH"
fi

echo "----------------------------------"
echo "当前版本: v$current"
echo "检测到 $update_type 版本变更"
echo "新版本: v$new_version"

echo "更新项目文件里的版本号..."
sed -i "s/APP_VERSION = \"[^\"]*\"/APP_VERSION = \"$new_version\"/" "$version_file"

echo "添加修改到 Git 暂存区..."
git add "$version_file"

echo "提交 Git 更改..."
git commit -m "chore(release): $new_version"

echo "创建 Git 标签: v$new_version ..."
git tag -a "v$new_version" -m "Release v$new_version"

current_version=$(get_current_version)
echo "当前项目的版本为: $current_version"

if [ "$current_version" == "$new_version" ]; then
  echo 操作完成，自动退出脚本
  exit 0
else
  echo 当前项目的版本与预期不符，建议手动检查文件！
  exit 1
fi
