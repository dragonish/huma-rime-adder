:: 运行猛击虎码加词器并自动重新部署小狼毫输入法程序

@echo off
echo 运行猛击虎码加词器...

:: 检查是否有参数传递
if not "%~1"=="" (
    :: 如果有参数，将参数传递给 huma-rime-adder.exe
    huma-rime-adder.exe -i %~1
) else (
    :: 如果没有参数则直接调用
    huma-rime-adder.exe
)

if %errorlevel% == 0 (
  echo 重新部署输入法...
  for /d %%i in ("C:\Program Files (x86)\Rime\weasel-*") do (
    if exist "%%i\WeaselDeployer.exe" (
      echo 在 "%%i\WeaselDeployer.exe" 中发现小狼毫输入法程序
      "%%i\WeaselDeployer.exe" /deploy
      echo 重新部署输入法完成
      goto :end
    )
  )
  echo 无法找到小狼毫输入法程序
) else if %errorlevel% == 1 (
  echo huma-rime-adder.exe 返回了错误代码 1。暂停执行...
  pause
  goto :end
)
:end
