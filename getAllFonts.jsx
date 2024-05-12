
function getPSFolder() {
    var userDataFolder = Folder.userData.fsName;
    var aescriptsFolder = userDataFolder.toString() + "/ConteAssistant/Icons";
    return aescriptsFolder.toString();
}
var folder = getPSFolder();



var command = 
'[System.Reflection.Assembly]::LoadWithPartialName("System.Drawing")\
$fontList = (New-Object System.Drawing.Text.InstalledFontCollection)\
$fontFile = "'+ folder +'/fonts.txt"\
if (Test-Path $fontFile) {\
    Remove-Item $fontFile\
}\
for ($i = 0; $i -lt $fontList.Families.Length; $i++) {\
    $fontNames = $fontList.Families[$i].Name\
    Add-Content $fontFile "$fontNames"\
}';



var psFile = File(folder+'/getFonts.ps1');
if (!psFile.exists) {
    psFile.open("w");
    psFile.write(command);
    psFile.close();

    var pathToPs1File = folder+'/getFonts.ps1';
    var executeIt = system.callSystem("cmd.exe /c PowerShell.exe -ExecutionPolicy UnRestricted -File " + pathToPs1File);
    $.sleep(500);
}
   

// get all fonts
var window = new Window("palette", "Installed Fonts", undefined);
var fontsDD = window.add("dropdownlist", undefined, []);
fontsDD.size = [220, 25];
var randomButton = window.add("button", undefined, "Random");
    
var fontFile = File(folder+"/fonts.txt");
if(!fontFile.exists){
    var executeIt = system.callSystem("cmd.exe /c PowerShell.exe -ExecutionPolicy UnRestricted -File " + pathToPs1File);
}
fontFile.open("r");
do {
    fontsDD.add("item", fontFile.readln());
    } while(!fontFile.eof);
fontFile.close();
fontsDD.selection = 0;



randomButton.onClick = function() {
        fontsDD.selection = Math.floor(Math.random() * fontsDD.items.length);
    }

window.center();
window.show();
