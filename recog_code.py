import numpy as np
import joblib
from PIL import Image, ImageDraw

digit_labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
alpha_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def binary_img(my_img, binary_array, threshold=180):
    """
    二值化照片
    @param my_img: 未二值化的灰度图片
    @param threshold:  二值化阈值
    @param binary_array:  二值像素矩阵字典
    @return: binary_array
    """
    for x in range(0, my_img.size[0]):
        for y in range(0, my_img.size[1]):
            pix = my_img.getpixel((x, y))
            if pix >= threshold | (x == 0) | (y == 0):
                binary_array[(x, y)] = 1  # 白色
            else:
                binary_array[(x, y)] = 0  # 黑色


def denoise(my_img, binary_array, surround_pt_nums=3):
    """
    降噪
    @param my_img:
    @param surround_pt_nums: 环绕的有效点数
    @param binary_array: 二值像素矩阵字典
    """
    for j in range(0, 5):
        for x in range(1, my_img.size[0]-1):
            for y in range(1, my_img.size[1]-1):
                surround_pt = 0
                if binary_array[(x, y)] == binary_array[(x-1, y)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x-1, y-1)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x-1, y+1)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x+1, y)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x+1, y-1)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x+1, y+1)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x, y-1)]:
                    surround_pt += 1
                if binary_array[(x, y)] == binary_array[(x, y+1)]:
                    surround_pt += 1

                if surround_pt < surround_pt_nums:
                    binary_array[(x, y)] = 1  # 噪点设置为白色


def save_img(filename, size, binary_array):
    """
    存储二值化图片
    @param filename: 图片文件名
    @param size: 图片尺寸
    @param binary_array: 二值像素矩阵字典
    @return:
    """
    my_img = Image.new("1", size)
    draw = ImageDraw.Draw(my_img)

    for x in range(size[0]):
        for y in range(size[1]):
            if (x == 0) or (y == 0) or (x == size[0]-1) or (y == size[1]-1):
                draw.point((x, y), 1)  # 去掉边缘上的噪声
            else:
                draw.point((x, y), binary_array[(x, y)])
    my_img.save(filename)


def crop_blank(filename):
    """
    去掉图片中多余的空白(因为每个字符的高度统一)
    @return:
"""
    img = Image.open(filename)
    box = (5, 8, img.size[0]-1, img.size[1]-7)
    img.crop(box=box).save('code_shrink.png')


def fix_img(filename):
    """
    修复图片，让图片更健壮
    @return:
    """
    img = Image.open(filename)
    binary_array = {}
    # 再次二值化
    for x in range(0, img.size[0]):
        for y in range(0, img.size[1]):
            pix = img.getpixel((x, y))
            if pix >= 128:
                binary_array[(x, y)] = 1  # 白色
            else:
                binary_array[(x, y)] = 0  # 黑色
    # 修复
    for x in range(1, img.size[0]-1):
        for y in range(1, img.size[1]-1):
            # 对角线上的白点小于等于1个
            diag_blanks = binary_array[(x-1, y-1)] + binary_array[(x-1, y+1)] + binary_array[(x+1, y-1)] + binary_array[(x+1, y+1)]
            # 水平垂直上都是黑点
            un_diag_blanks = binary_array[(x, y-1)] + binary_array[(x, y+1)] + binary_array[(x-1, y)] + binary_array[(x+1, y)]
            if (diag_blanks <= 1) and (un_diag_blanks == 0) and (binary_array[(x, y)] == 1):  # 自己也是白点
                binary_array[(x, y)] = 0
                if binary_array[(x-1, y-1)] == 1:
                    binary_array[(x-1, y-1)] = 0
                elif binary_array[(x-1, y+1)] == 1:
                    binary_array[(x-1, y+1)] = 0
                elif binary_array[(x+1, y-1)] == 1:
                    binary_array[(x+1, y-1)] = 0
                elif binary_array[(x+1, y+1)] == 1:
                    binary_array[(x+1, y+1)] = 0
            # 修复上下边缘
            if (y+1 == img.size[1]-1) or (y-1 == 0):
                blacks = diag_blanks + un_diag_blanks
                if (blacks == 1) and (binary_array[(x, y)] == 0):  # 只有一个白点且在边缘
                    binary_array[(x, y+1)] = 0
                    binary_array[(x, y-1)] = 0
    # 存储修复的图片
    my_img = Image.new("1", img.size)
    draw = ImageDraw.Draw(my_img)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            draw.point((x, y), binary_array[(x, y)])
    my_img.save('fix.png')


def cut_imgs(filename, cut_width=10, std_width=20):
    """
    切割图片
    @return:
    """
    threshold_nums = [0, 1, 2, 3, 4, 5, 6, 7]
    img = Image.open(filename)  # 二值化后的图片
    cut_times = 0    # 切割次数
    cube_size = (std_width, img.size[1])     # 最后的训练集图片大小
    cursor = 0                                 # 切割游标
    for x in range(5, img.size[0]-1):            # 从开始靠后5的地方开始遍历
        crop_box = (cursor, 0, x, img.size[1])   # 切割块
        col_sum = get_col_sum(img, x)
        left_sum = get_col_sum(img, x-1)
        right_sum = get_col_sum(img, x+1)
        if (col_sum == 0) and (left_sum == 0):  # 与左边连续空白
            continue
        if x == img.size[0] - 2:                # 判定到越界了
            cut_times += 1
            std_img(img.crop(box=crop_box), cube_size, 'c_' + str(cut_times) + '.png')
        # 类似于无穷符号的图像分布
        if (col_sum <= left_sum) and (col_sum <= right_sum) and (col_sum in threshold_nums):    # 如果最少黑点数在阈值内
            if (col_sum >= 5) and (not judge_disperse(img, x, col_sum)) and judge_lr(left_sum, col_sum, right_sum):
                # 如果黑点过多，也不是离散分布, 或左右相差很小则判定不切割
                continue
            if (x - cursor) < cut_width:  # 如果与上次切割点过近，则判定不切割, 即估计图片在宽度10以上
                continue
            cut_times += 1
            std_img(img.crop(box=crop_box), cube_size, 'c_' + str(cut_times) + '.png')
            cursor = x
        if cut_times >= 4:  # 如果进行了4次切割
            break
    if cut_times < 4:
        return False
    else:
        return True


def std_img(img, size, filename):
    my_img = Image.new("1", size)
    draw = ImageDraw.Draw(my_img)

    for x in range(size[0]):
        for y in range(size[1]):
            if (x >= img.size[0]) or (y >= img.size[1]):
                draw.point((x, y), 1)
            else:
                if img.getpixel((x, y)) > 128:
                    draw.point((x, y), 1)
                else:
                    draw.point((x, y), 0)
    my_img.save(filename)


def judge_lr(left, center, right):
    """
    判断邻近黑点数量
    @param left:
    @param center:
    @param right:
    @return:
    """
    if abs(left-center) <= 2 and abs(right-center) <= 2:
        return True
    else:
        return False


def judge_disperse(img, x, black_pts):
    """
    判断离散分布
    @param img:
    @param x:
    @param black_pts:
    @return:
    """
    disp_part = 0
    y = 0
    while y < img.size[1]:
        if img.getpixel((x, y)) < 128:
            disp_part += 1
            while y < img.size[1]:
                if img.getpixel((x, y)) < 128:
                    y += 1
                else:
                    break
        y += 1
    if (disp_part >= 2 and black_pts <= 6) or (disp_part >= 3 and black_pts >= 7):
        return True
    else:
        return False


def get_col_sum(img, x):
    """
    获取第x列的黑点数量
    @param img: 图片
    @param x: 列序号
    @return:
    """
    col_sum = 0
    for y in range(img.size[1]):
        if img.getpixel((x, y)) < 128:
            col_sum += 1
    return col_sum


def handle_img(img):
    binary_array = {}
    binary_img(img, binary_array)
    denoise(img, binary_array)
    save_img('code.png', img.size, binary_array)
    crop_blank("code.png")
    fix_img('code_shrink.png')
    cut_signal = cut_imgs('fix.png')
    if not cut_signal:
        return False
    else:
        # 识别两个数字
        dmodel = joblib.load('digit.pkl')
        d1_img = Image.open('c_1.png').getdata()
        d2_img = Image.open('c_3.png').getdata()
        sample1 = np.array(d1_img, dtype='int').reshape(1, -1)
        sample2 = np.array(d2_img, dtype='int').reshape(1, -1)
        ans_prob1 = dmodel.predict_proba(sample1).tolist()[0]
        ans_prob2 = dmodel.predict_proba(sample2).tolist()[0]
        d1 = digit_labels[ans_prob1.index(max(ans_prob1))]
        d2 = digit_labels[ans_prob2.index(max(ans_prob2))]
        # 识别两个字母
        amodel = joblib.load('alpha.pkl')
        a1_img = Image.open('c_2.png').getdata()
        a2_img = Image.open('c_4.png').getdata()
        sample1 = np.array(a1_img, dtype='int').reshape(1, -1)
        sample2 = np.array(a2_img, dtype='int').reshape(1, -1)
        ans_prob1 = amodel.predict_proba(sample1).tolist()[0]
        ans_prob2 = amodel.predict_proba(sample2).tolist()[0]
        a1 = alpha_labels[ans_prob1.index(max(ans_prob1))]
        a2 = alpha_labels[ans_prob2.index(max(ans_prob2))]

        return d1+a1+d2+a2


# if __name__ == '__main__':
#     ans = handle_img(Image.open('code.png').convert('L'))
#     print(ans)