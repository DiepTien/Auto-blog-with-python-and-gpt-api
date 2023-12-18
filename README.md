# Auto-blog-with-python-and-gpt-api
## Overview
This project consists of two Python scripts designed to automate the process of content creation and publishing for WordPress sites. The primary features include generating text content using GPT models, creating relevant images using DALL-E, and uploading the content to a WordPress site.
Video DEMO: [youtube.com]
## Files

### secrect.py
This file contains configuration and API keys necessary for the functioning of the autoblogging tool. It includes:
- OpenAI for text and image generation.
- WordPress API URL, username, and password for content uploading.
- Model names for GPT and DALL-E.
- Keywords and settings for content generation.

### Autoblog.py
This is the main script that automates content creation and publishing. Its features include:
- Generating text content using GPT models.
- Formatting content in HTML with SEO optimization.
- Creating images using DALL-E and uploading them to WordPress.
- Handling WordPress categories and tags.
- Logging for monitoring and debugging.

## Requirements
- Python 3.x
- OpenAI Python Library
- Requests Library

## Setup
1. Clone the repository.
2. Update `secrect.py` with your specific API keys and WordPress credentials.


## Usage
Run `Autoblog.py` to start the content generation and uploading process. The script will automatically generate and post content to the configured WordPress site.

## Security Note
Ensure that your API keys and credentials in `secrect.py` are kept secure and not exposed publicly.

## License
Apache License 2.0
Any questions can contact me via email: [diepminhanhtien@gmail.com].
