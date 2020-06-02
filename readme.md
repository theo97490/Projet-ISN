Pour que le module GameCore soit utilisable, il faut rajouter $WorkspaceFolder à python.autoComplete.extraPaths

Pour vscode settings.json:
{
    "python.pythonPath": "C:\\Users\\Theo\\AppData\\Local\\Programs\\Python\\Python38-32\\python.exe",
    "python.autoComplete.extraPaths": [
        "${workspaceFolder}/" ]
}