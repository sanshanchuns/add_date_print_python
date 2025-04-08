import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ExifTags
import pillow_heif
pillow_heif.register_heif_opener()

def get_photo_date(image_path):
    """获取图片日期（优先级：EXIF > 文件创建时间 > 当前时间）"""
    try:
        # 尝试获取EXIF信息
        with Image.open(image_path) as img:
            # 对于HEIC格式，需要特殊处理
            if image_path.lower().endswith('.heic'):
                heif_file = pillow_heif.read_heif(image_path)
                primary_image = heif_file.get_primary_image()
                exif_data = primary_image.exif
            else:
                exif_data = img._getexif() or {}
            
            if exif_data:
                # 查找拍摄时间标签（不同相机可能使用不同标签）
                for tag, value in exif_data.items():
                    decoded_tag = ExifTags.TAGS.get(tag, tag)
                    if decoded_tag in ["DateTimeOriginal", "DateTimeDigitized"]:
                        # 转换格式：将"YYYY:mm:dd HH:MM:SS"转换为datetime对象
                        exif_date = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        return exif_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"EXIF读取失败: {os.path.basename(image_path)} - {str(e)}")

    # 尝试获取文件创建时间
    try:
        # 获取文件的创建时间（在macOS上使用st_birthtime）
        creation_time = os.stat(image_path).st_birthtime
        file_date = datetime.fromtimestamp(creation_time)
        return file_date.strftime("%Y-%m-%d")
    except:
        pass

    # 全部失败时使用当前日期
    return datetime.now().strftime("%Y-%m-%d")

def calculate_font_size(img_width, img_height, base_size=1080, base_font_size=40):
    """根据图片较短边计算合适的字体大小"""
    shorter_side = min(img_width, img_height)
    return int(base_font_size * (shorter_side / base_size))

def add_kodak_date(directory, font_path='digital-7.ttf'):
    # 配置参数
    base_font_size = 40  # 基准字体大小（对应1080px的较短边）
    text_color = (255, 165, 0)  # 橙色
    date_format = "%Y-%m-%d"  # 柯达经典格式
    padding_ratio = 0.02  # 边距比例（相对于图片宽度）

    # 加载数码字体（需自行下载字体文件）
    try:
        base_font = ImageFont.truetype(font_path, base_font_size)
    except:
        base_font = ImageFont.truetype("arial.ttf", base_font_size)
        print("警告：未找到数码字体，已使用备用字体")

    # 遍历目录中的图片
    for filename in os.listdir(directory):
        # 检查文件扩展名（包括HEIC格式）
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.heic')):
            filepath = os.path.join(directory, filename)
            
            # 获取照片拍摄日期
            current_date = get_photo_date(filepath)  # ⭐️改为动态获取日期
            
            try:
                with Image.open(filepath).convert("RGBA") as img:
                    # 计算当前图片的字体大小和边距
                    font_size = calculate_font_size(img.width, img.height)
                    padding = int(min(img.width, img.height) * padding_ratio)
                    
                    # 加载对应大小的字体
                    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.truetype("arial.ttf", font_size)
                    
                    # 创建透明图层
                    txt = Image.new("RGBA", img.size, (0,0,0,0))
                    draw = ImageDraw.Draw(txt)
                    
                    # 计算文字位置（使用textbbox替代textsize）
                    bbox = draw.textbbox((0, 0), current_date, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = img.width - text_width - padding
                    y = img.height - text_height - padding
                    
                    # 添加文字（带黑色描边模拟数码效果）
                    draw.text((x-1, y-1), current_date, font=font, fill=(0,0,0,255))  # 黑色描边
                    draw.text((x+1, y+1), current_date, font=font, fill=(0,0,0,255))
                    draw.text((x, y), current_date, font=font, fill=text_color)
                    
                    # 合并图层并保存
                    combined = Image.alpha_composite(img, txt)
                    output_path = os.path.splitext(filepath)[0] + "_dated.png"
                    combined.save(output_path)
                    print(f"已处理：{filename}")
                    
            except Exception as e:
                print(f"处理失败：{filename} - {str(e)}")

if __name__ == "__main__":
    # 使用示例（需替换为实际路径）
    add_kodak_date(
        directory="/Users/leozhu/Desktop/test",
        font_path="/Users/leozhu/Desktop/led-digital-7-1.ttf"  # 推荐下载数码字体
    )