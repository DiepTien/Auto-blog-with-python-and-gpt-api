import requests
import time
import logging
import re
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from secrect import *
import random
import openai

# Tạo logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Tạo handler để ghi log vào terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Tạo định dạng cho log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Gán handler cho logger
logger.addHandler(console_handler)

class WordPressPostUploader:
    def __init__(self, wordpress_api_url, username, password, api_url_img_model, headers):
        self.wordpress_api_url = wordpress_api_url
        self.username = username
        self.password = password
        self.api_url_img_model = api_url_img_model
        self.headers = headers

    def create_content(self, topic):
        logger.info('Creating content...')
        prompt = ChatPromptTemplate.from_template(f'''
        Tạo bài viết tiếng việt chủ đề: {topic}.
        ''')
        model = ChatOpenAI(model_name=gpt_model, temperature=gpt_temperature, openai_api_key=open_ai_key)
        functions = [
            {
                "name": "wordpress_article",
                "description": "wordpress article",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "a title of the article"},
                        "content": {"type": "string", "description": "Content of the article"},
                        "status": {"type": "string", "description": "publish"},
                        "format": {"type": "string", "description": "standard"},
                        "categories": {"type": "array",
                                       "items": {"type": "string", "description": "Categorize articles"}},
                        "tags": {"type": "array",
                                 "items": {"type": "string", "description": "Tags related to the article in a list"}},
                        "featured_media": {"type": "string",
                                           "description": "description of the image illustrating the article "},
                    },
                    "required": ["title", "content", "status", "format", "categories", "tags", "featured_media"],
                },
            }
        ]
        chain = (prompt | model.bind(function_call={"name": "wordpress_article"},
                                     functions=functions) | JsonOutputFunctionsParser())
        result = chain.invoke({"topic": topic})
        logger.info('Content created.')
        print(result)
        return result

    def cover_content(self, content):
        messages = [
            {"role": "system", "content": f'''You are a helpful assistant.'''},
            {"role": "user", "content": f'''Tạo bài viết có độ dài không dưới 700 từ với chủ đề: {content}.Trình bày bài viết dưới dạng html và hãy đảm bảo tối ưu từ khóa tìm kiếm, thêm ngẫu nhiên các thẻ img( tối đa 3 thẻ) với format như sau <img src='([^']*)' alt='([^']*)'> vào các đoạn nội dung chính trong bài viết sau( thẻ alt phải mô tả chi tiết hình ảnh minh họa cho đoạn nội dung đó và viết bằng tiếng anh). Chỉ trả về kết quả'''}
        ]
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model_4,  # Replace with your specific GPT model name
                messages=messages
            )
            answer = response['choices'][0]['message']['content']
        except Exception as e:
            answer = content
        return answer


    def cover_featured_media(self, title):
        messages = [
            {"role": "system", "content": f"You are a helpful assistant."},
            {"role": "user",
             "content": f'''Miêu tả hình ảnh minh hoạ cho bài viết có tiêu đề "{title}" nên trông như thế nào. Trả lời bằng tiếng anh.'''}
        ]
        try:
            response = openai.ChatCompletion.create(
                model=gpt_model,  # Replace with your specific GPT model name
                messages=messages
            )
            answer = response['choices'][0]['message']['content']
        except Exception as e:
            answer = title
        return answer
    def image_from_model(self, image_des):
        response = openai.Image.create(
            model= dalle_model,
            prompt=image_des,
            n=1,
            size="1024x1024"
        )
        # Assume the response contains a direct URL to the image
        image_url = response['data'][0]['url']
        response = requests.get(image_url)
        return response

    def upload_image_to_wordpress(self, image_des):
        logger.info('Uploading image to WordPress...')
        url = self.wordpress_api_url + "/wp-json/wp/v2/media"
        image_data = self.image_from_model(image_des)
        if image_data.status_code == 200:
            files = {'file': ('image.jpg', image_data.content)}
            response = requests.post(url, files=files, auth=(self.username, self.password))
            if response.status_code == 201:
                image_data = response.json()
                image_url_in_wp = image_data
                logger.info('Image uploaded successfully.')
                return image_url_in_wp
            else:
                logger.error('Failed to upload the image to WordPress.')
                return None
        else:
            logger.error('Failed to fetch the image data from the URL.')
            return None
    def process_content(self, input_dict):
        input_dict['content'] = self.cover_content(input_dict['title'])
        print(input_dict['content'])
        input_dict['featured_media'] = self.cover_featured_media(input_dict['title'])
        print(input_dict['featured_media'])
        logger.info('Processing content...')
        content = input_dict['content']
        img_replacements = {}
        featured_media_replacement = None
        for match in re.finditer(r"<img src='([^']*)' alt='([^']*)'>", content):
            old_src = match.group(1)
            alt_description = match.group(2)
            new_src = self.upload_image_to_wordpress(alt_description)['source_url']
            img_replacements[old_src] = new_src
        for old_src, new_src in img_replacements.items():
            content = content.replace(f"<img src='{old_src}' alt", f"<img src='{new_src}' alt")
        input_dict['content'] = content
        featured_media_url = input_dict['featured_media']
        featured_media_id = self.upload_image_to_wordpress(featured_media_url)['id']
        input_dict['featured_media'] = str(featured_media_id)
        logger.info('Content processed.')
        # print(input_dict)
        return input_dict


    def check_category_existence(self, category_name_to_check):
        logger.info('Checking category existence...')
        url = self.wordpress_api_url + "/wp-json/wp/v2/categories"
        page_tag_start = 1
        categories = []
        while True:
            params = {'per_page': 100, 'page': page_tag_start}
            response = requests.get(url, auth=(self.username, self.password), params=params)
            if len(response.json()) > 0:
                categories.extend(response.json())
            else:
                break
            page_tag_start += 1
        category_exists = False
        category_id = None
        for category in categories:
            if category['name'] == category_name_to_check:
                category_exists = True
                category_id = category['id']
                break
        if not category_exists:
            new_category_data = {'name': category_name_to_check}
            response = requests.post(url, json=new_category_data, auth=(self.username, self.password))
            if response.status_code == 201:
                category_id = response.json()['id']
                logger.info('New category created successfully.')
            else:
                logger.error('Error occurred while creating category: ', response.text)
        logger.info('Category existence checked.')
        return category_id

    def check_tag_existence(self, tag_name_to_check):
        logger.info('Checking tag existence...')
        url = self.wordpress_api_url + "/wp-json/wp/v2/tags"
        page_tag_start = 1
        tag_id = None
        tags = []

        while True:
            params = {'per_page': 100, 'page': page_tag_start}
            response = requests.get(url, auth=(self.username, self.password), params=params)
            if len(response.json()) > 0:
                tags.extend(response.json())
            else:
                break
            page_tag_start += 1

        tag_exists = False
        for tag in tags:
            if tag['name'].lower() == tag_name_to_check.lower():
                tag_exists = True
                tag_id = tag['id']
                break
        if not tag_exists:
            new_tag_data = {'name': tag_name_to_check}
            response = requests.post(url, json=new_tag_data, auth=(self.username, self.password))
            if response.status_code == 201:
                tag_id = response.json()['id']
                logger.info('New tag created successfully.')
            else:
                logger.error(f'Error occurred while creating tag: {tag_name_to_check}', response.text)
        logger.info('Tag existence checked.')
        return tag_id

    def create_post(self, topic):
        logger.info('Creating post...')
        content = self.create_content(topic)
        data = self.process_content(content)
        if 'categories' in data:
            for i in range(len(data['categories'])):
                data['categories'][i] = self.check_category_existence(data['categories'][i])
        if 'tags' in data:
            for i in range(len(data['tags'])):
                data['tags'][i] = self.check_tag_existence(data['tags'][i])
        url = self.wordpress_api_url + "/wp-json/wp/v2/posts"
        response = requests.post(url, auth=(self.username, self.password), json=data)
        if response.status_code == 201:
            logger.info('Post created successfully.')
        else:
            logger.error('Failed to create post: ' + response.text)


def main():
    hugging_face_api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    uploader = WordPressPostUploader(wordpress_api_url, wordpress_username, wordpress_password, hugging_face_api_url,
                                     hugging_face_headers)
    # while True:
    #     random.shuffle(art_keywords)  # Xáo trộn danh sách ngẫu nhiên
    #     for keyword in art_keywords:
    start_time = time.time()
    uploader.create_post(keyword)
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Post execution time: {execution_time} seconds")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"Program execution time: {execution_time} seconds")
