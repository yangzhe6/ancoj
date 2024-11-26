import os
import re
import chardet
import pandas as pd

def extract_astronomy_data(folder_path):
    # 初始化一个空的DataFrame来存储结果
    results = pd.DataFrame(columns=[
        'id', 'Type', 'Dates', 'Observatory', 
        'Reference Frame', 'Centre of Frame', 'Epoch of Equinox', 
        'Time Scale', 'Reduction', 'Coordinates', 'Diffraction', 'Receptor', 
        'Telescope', 'Observers', 'Relative To'
    ])

    # 初始化字典来记录成功和失败的项
    status = {
        'success': [],
        'failures': {}
    }

    # 遍历文件夹内的所有HTML文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.html'):
            file_path = os.path.join(folder_path, filename)
            file_id = os.path.splitext(filename)[0]  # 获取不包含后缀的文件名
            
            # 检测文件编码
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

            # 读取文件内容
            with open(file_path, 'r', encoding=encoding) as file:
                html_content = file.read()
            
            # 初始化一个字典来存储当前文件的结果
            current_file_results = {'id': file_id}
            
            # 使用正则表达式提取Contents.部分的type, dates, observatory
            contents_patterns = {
                'Type': r'\btype:\s*(.+)',
                'Dates': r'\bdates:\s*(.+)',
                'Observatory': r'\bobservatory:\s*(.+)'
            }
            
            # 提取Contents.部分的内容
            for key, pattern in contents_patterns.items():
                regex = re.compile(pattern)
                match = regex.search(html_content)
                if match:
                    current_file_results[key] = match.group(1).strip()
                    status['success'].append(filename)
                else:
                    if filename not in status['failures']:
                        status['failures'][filename] = []
                    status['failures'][filename].append(key)
            
            # 提取Informations.到Comments.或Format.之间的全部内容
            informations_pattern = r'Informations\..*?(?=\b(Comments|Format)\.)'
            informations_match = re.search(informations_pattern, html_content, re.DOTALL)
            if informations_match:
                informations_content = informations_match.group(0).strip()
                
                # 提取Informations.部分的各个字段
                fields_patterns = {
                    'Reference Frame': r'\breference frame:\s*(.+)',
                    'Centre of Frame': r'\bcentre of frame:\s*(.+)',
                    'Epoch of Equinox': r'\bepoch of equinox:\s*(.+)',
                    'Time Scale': r'\btime scale:\s*(.+)',
                    'Reduction': r'\breduction:\s*(.+)',
                    'Coordinates': r'\bcoordinates:\s*(.+)',
                    'Diffraction': r'\bdiff. refraction:\s*(.+)',
                    'Receptor': r'\breceptor:\s*(.+)',
                    'Telescope': r'\btelescope:\s*(.+)',
                    'Observers': r'\bobservers:\s*(.+)'
                }
                
                for field, pattern in fields_patterns.items():
                    regex = re.compile(pattern)
                    match = regex.search(informations_content)
                    if match:
                        current_file_results[field] = match.group(1).strip()
                    else:
                        current_file_results[field] = None  # 如果字段不存在，则设为None
                
                # 处理可能有多个relative to的情况
                relative_pattern = r'\brelative to:\s*(.+)'
                relative_matches = re.findall(relative_pattern, informations_content)
                if relative_matches:
                    current_file_results['Relative To'] = '; '.join(relative_matches)
            
            else:
                if filename not in status['failures']:
                    status['failures'][filename] = []
                status['failures'][filename].append('Informations')
            
            # 将提取的内容添加到DataFrame中
            results = results.append(current_file_results, ignore_index=True)

    # 将结果保存到CSV文件
    results.to_csv('./result/Informations.csv', index=False)

    # 打印成功和失败的项
    print(f"成功提取 {len(status['success'])} 项")
    if status['failures']:
        print("失败的项有：")
        for filename, missing_keys in status['failures'].items():
            print(f"文件 {filename} 缺失以下信息：{', '.join(missing_keys)}")
