# 1. 创建 README.md 文件
echo "# nga-monitor" >> README.md

# 2. 初始化 Git 仓库
git init

# 3. 添加文件到暂存区
git add README.md

# 4. 提交到本地仓库
git commit -m "first commit"

# 5. 重命名主分支
git branch -M main

# 6. 关联远程仓库
git remote add origin https://github.com/milakakok/nga-monitor.git

# 7. 推送到 GitHub
git push -u origin main
