# Agents-openai-langchain

#### Tutorial by [![N|Solid](https://vultureprime-research-center.s3.ap-southeast-1.amazonaws.com/vulturePrimeLogo.png)](https://vultureprime.com)

## บทความ
- [วิธีการสร้าง Basic Agents ด้วย Langchain [พร้อม Code ตัวอย่าง]](https://www.vultureprime.com/)

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
https://github.com/vultureprime/deploy-ai-model.git && cd ./deploy-ai-model/aws-example/text-to-sql-openai-postgresSQL
```

4. Install dependencies
```
pip install -r requirements.txt
```

5. Run
```
uvicorn app:app --reload --host 0.0.0.0 --port 3000
```

## License 
MIT
