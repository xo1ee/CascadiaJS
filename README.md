# Instructions to run application locally:

## This will run the backend
### In the terminal of your IDE of choice:
pip install -r
 geo_service/requirements.txt
python -m uvicorn main:app --reload --port 8000

## This will run the front end
### In a seperate terminal:
 npx create-next-app@latest web --typescript --eslint --app --src-dir --use-npm --disable-git --yes
 cd web
 npm run dev
 
## API Keys
In the web directory, create a .env.local folder containing the following:
- NEXT_PUBLIC_API_URL
- NEXT_PUBLIC_MAPBOX_TOKEN
- MAPBOX_TOKEN
