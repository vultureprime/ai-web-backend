# Chatbot-openai-llamindex

#### Tutorial by [![N|Solid](https://vultureprime-research-center.s3.ap-southeast-1.amazonaws.com/vulturePrimeLogo.png)](https://vultureprime.com)

## บทความ
- [วิธีการสร้าง Chatbot ด้วย Agent และ RAG [พร้อม Code ตัวอย่าง]](https://www.vultureprime.com/)

## สิ่งที่ต้องมี
- [AWS](https://aws.amazon.com/) Account 
- [Open AI](https://openai.com/) API Key

## สิ่งที่ต้องเตรียม
- OPENAI_API_KEY

## ขั้นตอน 
1. เข้าใช้งาน AWS EC2 
2. สร้าง Virtual Machine โดยเลือกเป็น t4g.medium (CPU)

3. Git clone 
```
https://github.com/vultureprime/ai-web-backend.git && cd ./ai-web-backend/Chatbot-openai-llamindex
```

4. Install dependencies
```
pip install -r requirements.txt && mkdir data && wget "https://www.dropbox.com/s/948jr9cfs7fgj99/UBER.zip?dl=1" -O data/UBER.zip && unzip data/UBER.zip -d data
```

5. Run
```
uvicorn app:app --reload --host 0.0.0.0 --port 3000
```

## License 
MIT