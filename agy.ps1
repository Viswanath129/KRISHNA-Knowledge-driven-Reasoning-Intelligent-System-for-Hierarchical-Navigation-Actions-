$sub = $args[0]
if ($sub -in @('gui', 'uacc', 'voice', 'execute')) {
    & python "C:\Users\kasiv\AppData\Local\agy\bin\agy_cli.py" $args
} else {
    & "C:\Users\kasiv\AppData\Local\agy\bin\agy_core.exe" $args
}
