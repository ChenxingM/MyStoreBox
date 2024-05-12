{
    // 创建一个新的 UI 面板
    var mainWindow = new Window("palette", "Layer Info Exporter", undefined);
    mainWindow.orientation = "column";

    // 添加一个按钮到 UI 面板
    var exportButton = mainWindow.add("button", undefined, "Export Layer Info");
    var importButton = mainWindow.add("button", undefined, "Import Layer Info");

    exportButton.onClick = function() {
        try {
            // 获取当前的活动合成
            var comp = app.project.activeItem;
            
            // 如果当前没有活动的合成，弹出警告
            if (!comp || !(comp instanceof CompItem)) {
                alert("No comp selected!");
                return;
            }

            // 准备存储图层信息的字符串
            var layerInfoStr = "";

            // 需要收集的属性名
            var requiredProps = ["ADBE Anchor Point", "ADBE Position", "ADBE Scale", "ADBE Rotate Z","ADBE Opacity"];

            // 遍历合成中的所有图层
            for (var i = 1; i <= comp.numLayers; i++) {
                var layer = comp.layer(i);

                // 收集图层的相关信息
                layerInfoStr += "Layer Name: " + layer.name + "\n";

                var transformGroup = layer.property("ADBE Transform Group");

                // 遍历需要的属性
                for (var j = 0; j < requiredProps.length; j++) {
                    var prop = transformGroup.property(requiredProps[j]);

                    if (prop) {
                        layerInfoStr += "Property Name: " + prop.name + "\n";

                        // 如果属性有关键帧，那么收集所有关键帧的值和时间
                        if (prop.numKeys > 0) {
                            for (var k = 1; k <= prop.numKeys; k++) {
                                layerInfoStr += "Key " + k + ":\n";
                                layerInfoStr += "Time: " + prop.keyTime(k) + "\n";
                                layerInfoStr += "Value: " + prop.keyValue(k).toString() + "\n";
                                layerInfoStr += "In Interpolation Keyframe Type: " + prop.keyInInterpolationType(k) + "\n";
                                layerInfoStr += "Out Interpolation Keyframe Type: " + prop.keyOutInterpolationType(k) + "\n";
                            }
                        } else {
                            // 如果属性没有关键帧，那么只收集当前的值
                            layerInfoStr += "Value: " + prop.value.toString() + "\n";
                        }

                        layerInfoStr += "------------------------\n";
                    }
                }

                layerInfoStr += "================================\n";
            }

            // 创建一个新的文件对话框以保存文本文件
            var file = File.saveDialog("Save Layer Info", "*.txt");

            // 打开文件，写入数据，然后关闭文件
            if (file) {
                file.open("w");
                file.write(layerInfoStr);
                file.close();
            }
        } catch (error) {
            alert("An error occurred: " + error.toString());
        }
    };



    importButton.onClick = function() {
        try {
            // 获取当前的活动合成
            var comp = app.project.activeItem;

            // 如果当前没有活动的合成，弹出警告
            if (!comp || !(comp instanceof CompItem)) {
                alert("No comp selected!");
                return;
            }

            // 创建一个新的文件对话框以选择文本文件
            var file = File.openDialog("Select Layer Info File", "*.txt");

            // 如果用户选择了一个文件，打开它并读取其内容
            if (file) {
                file.open("r");
                var layerInfoStr = file.read();
                file.close();

                // 将读取的字符串分解为行
                var lines = layerInfoStr.split("\n");

                var currentLayer, currentProperty, currentKey;

                // 通过读取的行，将信息应用到对应的图层和属性
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i];

                    if (line.indexOf("Layer Name: ") === 0) {
                        var layerName = line.substring("Layer Name: ".length);
                        currentLayer = comp.layers.byName(layerName);
                    } else if (line.indexOf("Property Name: ") === 0) {
                        var propName = line.substring("Property Name: ".length);
                        if (currentLayer) {
                            currentProperty = currentLayer.property("ADBE Transform Group").property(propName);
                        }
                    } else if (line.indexOf("Key ") === 0) {
                        if (currentProperty) {
                            var keyIndex = parseInt(line.substring("Key ".length));
                            var timeLine = lines[++i];
                            var valueLine = lines[++i];
                            var typeLine = lines[++i];


                            var keyTime = parseFloat(timeLine.substring("Time: ".length));
                            var keyValueString = valueLine.substring("Value: ".length).split(',');

                            

                            var keyValue = [];
                            for (var j = 0; j < keyValueString.length; j++) {
                                keyValue[j] = parseFloat(keyValueString[j]);
                            }

                            currentProperty.setValueAtTime(keyTime, keyValue);
                            var outTypeLine = lines[i+1];
                            currentProperty.setInterpolationTypeAtKey(keyIndex, parseInt(typeLine.replace("In Interpolation Keyframe Type: ","")),parseInt(outTypeLine.replace("Out Interpolation Keyframe Type: ","")));
                            currentKey = keyIndex;
                           
                        }
                    } else if (line.indexOf("Value: ") === 0) {
                        if (currentProperty) {
                            var valueString = line.substring("Value: ".length).split(',');

                            var value = [];
                            for (var j = 0; j < valueString.length; j++) {
                                value[j] = parseFloat(valueString[j]);
                            }

                            currentProperty.setValue(value);
                        }
                    }
                }

                alert("Layer info imported successfully!");
            }
        } catch (error) {
            alert("An error occurred: " + error.toString());
        }
    };
    // 显示 UI 面板
    mainWindow.show();
}
