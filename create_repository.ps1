# 创建GitHub仓库并推送代码的步骤

# 1. 请先访问 https://github.com/new 创建一个名为 "NarutoRound" 的空仓库
Write-Host "请先访问 https://github.com/new 创建一个名为 'NarutoRound' 的新仓库"
Write-Host "创建仓库时，不要初始化README，不要添加.gitignore，不要添加license"
Write-Host "创建完成后，请按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 2. 推送代码到远程仓库
Write-Host "`n正在推送代码到远程仓库..."
git push -u origin master

Write-Host "`n如果推送成功，您的代码已经上传到GitHub！"
Write-Host "可以通过 https://github.com/8avalon8/NarutoRound 访问您的项目" 