from moviepy.editor import VideoFileClip
from colorthief import ColorThief
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import os
import sys
from collections import deque
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QRadioButton, QFileDialog, QComboBox
from PyQt5.QtCore import QTimer

os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/local/bin/ffmpeg"

myfont = ImageFont.truetype('SourceHanMono-Medium.otf', 60)  # 设置字体
myfont0 = ImageFont.truetype('SourceHanMono-Medium.otf', 20)  # 设置字体

def add_color_palette_to_frame(frame_path, colors):
    frame = Image.open(frame_path)
    width, height = frame.size
    color_block_height = 70
    new_height = height + color_block_height
    color_block_width = width // len(colors)

    new_frame = Image.new("RGB", (width, new_height))
    new_frame.paste(frame, (0, 0))

    draw = ImageDraw.Draw(new_frame)


    for i, color in enumerate(colors):
        hex_color = rgb_to_hex(color)
        text_color = get_text_color(color)
        block_start = i * color_block_width
        draw.rectangle([block_start, height, block_start + color_block_width, new_height], fill=tuple(color))
        draw.text((block_start + 10, height + 10), hex_color, fill=text_color, font=myfont0)

    new_frame.save(frame_path)

def extract_frame_number(filename):
    basename = os.path.basename(filename)  # 获取文件名（去除路径）
    number_part = basename.split('_')[1]  # 假设文件名格式为 "frame_10.png"
    frame_number = number_part.split('.')[0]  # 获取不含扩展名的部分
    return frame_number


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def get_text_color(rgb):
    return 'black' if (sum(rgb) / 3) > 128 else 'white'




def create_summary_image(color_data, video_path):
    num_frames = len(color_data)
    num_colors_per_palette = max(len(colors) for colors in color_data.values())
    color_block_width = 400  # 颜色块宽度
    color_block_height = 280  # 颜色块高度
    text_margin = 300  # 文本边距

    summary_image_width = num_colors_per_palette * color_block_width + text_margin
    summary_image_height = num_frames * color_block_height

    summary_image = Image.new('RGB', (summary_image_width+400, summary_image_height+600))
    draw = ImageDraw.Draw(summary_image)

    for i, (frame, colors) in enumerate(color_data.items()):
        frame_number = extract_frame_number(frame)
        draw.text((15, i * color_block_height + color_block_height/2), f'{frame_number}f', fill='white', font=myfont)

        for j, color in enumerate(colors):
            hex_color = rgb_to_hex(color)
            text_color = get_text_color(color)
            block_x_start = j * color_block_width + text_margin
            block_x_end = block_x_start + color_block_width
            block_y_start = i * color_block_height
            block_y_end = block_y_start + color_block_height

            draw.rectangle(
                [block_x_start, block_y_start, block_x_end, block_y_end],
                fill=tuple(color)
            )
            draw.text(
                (block_x_start + 5, block_y_start + 5),
                hex_color, fill=text_color, font=myfont
            )
        draw.text(( 500, summary_image_height + 100), f'颜色分析自视频 {os.path.basename(video_path)}', fill='white', font=myfont)

    return summary_image


def create_color_table(color_data):
    formatted_data = []
    for frame, colors in color_data.items():
        frame_number = extract_frame_number(frame)
        color_strings = [f"({r},{g},{b})" for r, g, b in colors]
        row = [frame_number] + color_strings
        formatted_data.append(row)

    column_names = ['Frame'] + [f'Color {j+1}' for j in range(len(max(color_data.values(), key=len)))]
    return pd.DataFrame(formatted_data, columns=column_names)

class ColorAnalysisUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Video Path Input
        self.videoPathInput = QLineEdit(self)
        self.browseButton = QPushButton("浏览", self)
        self.browseButton.clicked.connect(self.browseFile)
        layout.addWidget(QLabel("第一步: 选择视频文件"))
        layout.addWidget(self.videoPathInput)
        layout.addWidget(self.browseButton)

        # 第二步：设置间隔的标签
        layout.addWidget(QLabel("第二步: 设置间隔"))

        # 水平布局：输入框和下拉菜单
        intervalLayout = QHBoxLayout()
        self.intervalInput = QLineEdit(self)
        self.intervalInput.setFixedWidth(60)  # 设置输入框宽度
        self.intervalType = QComboBox(self)
        self.intervalType.addItems(["秒", "帧"])
        intervalLayout.addWidget(self.intervalInput)
        intervalLayout.addWidget(self.intervalType)
        self.intervalInput.setText("15")  # 设置默认值

        layout.addLayout(intervalLayout)  # 将水平布局添加到垂直布局中


        # 算法选择
        self.algoButton1 = QRadioButton("颜色窃取法(速度快)")
        self.algoButton2 = QRadioButton("K聚类法(速度慢 更准确)")
        #self.colorCountInput = QLineEdit(self)  # 或者使用 QSpinBox
        layout.addWidget(QLabel("第三步: 选择算法"))
        layout.addWidget(self.algoButton1)
        layout.addWidget(self.algoButton2)
        self.algoButton1.setChecked(True)
        # 颜色数量设置部分
        colorCountLayout = QHBoxLayout()  # 水平布局
        self.colorCountInput = QLineEdit(self)
        self.colorCountInput.setFixedWidth(60)  # 设置输入框宽度
        colorCountLayout.addWidget(QLabel("设置颜色数量"))
        colorCountLayout.addWidget(self.colorCountInput)
        # 设置默认颜色数量
        self.colorCountInput.setText("6")

        layout.addLayout(colorCountLayout)  # 将水平布局添加到垂直布局中

        # Start Button
        self.startButton = QPushButton("开始分析", self)
        layout.addWidget(QLabel("第四步: 开始！"))
        layout.addWidget(self.startButton)
        self.startButton.clicked.connect(self.performColorAnalysis)

        layout.addWidget(QLabel("作者：千石まよひ JAN 2024"))

        self.setLayout(layout)
        self.setWindowTitle('视频颜色分析工具 1.0')
        self.messageQueue = deque()
        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.processQueue)
        self.updateTimer.start(100)  # 设置定时器，例如每100毫秒触发一次

    def processQueue(self):
        if self.messageQueue:
            message = self.messageQueue.popleft()
            self.outputLabel.setText(message)

    def updateOutput(self, text):
        self.messageQueue.append(text)


    def browseFile(self):
        fname = QFileDialog.getOpenFileName(self, '打开视频', os.path.expanduser("~/Desktop"))
        if fname[0]:
            self.videoPathInput.setText(fname[0])

    def selectSaveLocation(self):
        folder = QFileDialog.getExistingDirectory(self, "选择目录")
        if folder:
            self.savePathInput.setText(folder)

    def extract_frames(self, video_path, interval, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)  # 创建子文件夹

        clip = VideoFileClip(video_path)
        fps = clip.fps  # 获取视频的帧率
        frames = []
        for t in range(0, int(clip.duration), interval):
            frame = clip.get_frame(t)
            current_frame = int(t * fps)  # 计算当前帧数
            frame_path = os.path.join(folder, f'frame_{current_frame}.png')  # 在子文件夹中保存
            print(f'正在保存第{t}秒的帧 (帧号: {current_frame})...')
            Image.fromarray(frame).save(frame_path)
            frames.append(frame_path)
        return frames

    def k_means_algorithm(self, image_path, num_clusters):
        frame_number = os.path.basename(image_path).split('_')[-1].split('.')[0]
        print(f'正在分析帧 {frame_number}')
        image = Image.open(image_path)
        image_np = np.array(image)
        pixels = image_np.reshape(-1, 3)

        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(pixels)

        centers = kmeans.cluster_centers_
        centers = centers.astype(int)  # 将中心点颜色值转换为整数

        # 按亮度排序
        centers = sorted(centers, key=lambda x: sum(x), reverse=True)

        return centers

    def color_theif_alg(self, image_path, num_clusters):
        frame_number = os.path.basename(image_path).split('_')[-1].split('.')[0]
        print(f'正在分析帧 {frame_number}')
        color_thief = ColorThief(image_path)
        palette = color_thief.get_palette(color_count=num_clusters)
        palette.sort(key=lambda x: sum(x), reverse=True)
        return palette

    def performColorAnalysis(self):
        self.outputLabel.setText("准备开始...")
        video_path = self.videoPathInput.text()
        video_name = os.path.basename(video_path).split('.')[0]
        interval_value = int(self.intervalInput.text())
        interval_type = self.intervalType.currentText()

        if interval_type == "帧":
            # 将帧转换为秒
            clip = VideoFileClip(video_path)
            fps = clip.fps  # 获取视频的帧率
            interval = interval_value / fps
        else:
            interval = interval_value
        use_algo0 = self.algoButton1.isChecked()

        video_path0 = self.videoPathInput.text().split('.')[0]
        print(f'帧文件保存到 {video_path0}/Extracted_Frames_from_{video_name}')
        print(f'颜色总结图像和颜色数据csv保存到 {video_path0}...')
        print(f'开始分析视频 {video_name}...')
        folder_name = os.path.join(video_path0, f"Extracted_Frames_from_{video_name}")

        frames = self.extract_frames(video_path, interval, folder=folder_name)
        color_num = int(self.colorCountInput.text())
        color_data = {frame: (
            self.color_theif_alg(frame, color_num) if use_algo0 else self.k_means_algorithm(frame, color_num)) for frame in frames}
        summary_image = create_summary_image(color_data, video_path)
        color_table = create_color_table(color_data)
        summary_image_name = f"{video_name}_color_summary.png"
        color_table_name = f"{video_name}_color_data.csv"
        # 保存结果
        print(f'保存颜色汇总图像... {summary_image_name}')
        summary_image.save(summary_image_name, "PNG", dpi=(300, 300))
        print(f'保存颜色数据表CSV... {color_table_name}')
        color_table.to_csv(color_table_name)
        print("完成！")
        for frame, colors in color_data.items():
            frame_number = os.path.basename(frame).split('_')[-1].split('.')[0]
            print(f'将颜色绘制在帧 {frame_number}')
            add_color_palette_to_frame(frame, colors)
        print("完成！")
        print(f'分析结果保存在 {os.getcwd()}')
        self.outputLabel.setCursorPosition(0)  # 将光标移动到开头




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ColorAnalysisUI()
    ex.show()
    sys.exit(app.exec_())




"""
video_path = "qingtong.mp4"
interval = 30  # 每15秒取一帧

frames = extract_frames(video_path, interval)
color_data = {frame: analyze_colors(frame) for frame in frames}
summary_image = create_summary_image(color_data, video_path)
color_table = create_color_table(color_data)

summary_image.save("color_summary.png", "PNG", dpi=(300, 300))  # 设置DPI
color_table.to_csv("color_data.csv")

image_path = 'color_summary.png'  # 您保存的图像文件路径
img = mpimg.imread(image_path)

# 显示图像
plt.imshow(img)
plt.axis('off')  # 不显示坐标轴
plt.show()
"""




"""
# 应用于每一帧
for frame, colors in color_data.items():
    print("Adding color palette to", frame)
    add_color_palette_to_frame(frame, colors)


print("Done!")
"""