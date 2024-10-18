export DATABASE_URL=postgresql://irawo_bot_user:QIVDWskL73TP2Ks6Rte9SgYQIjYtC5f9@dpg-cs96rgqj1k6c73e0h4b0-a.oregon-postgres.render.com/irawo_bot
export DATABASE_SECRET=true
export CLOUDINARY_URL=cloudinary://284158535787842:ULU5OZCTtEtJP_VdPAQ_YGq3KI8@dgzhksp9f
export COHERE_KEY=knjTpWu3Tca6nWuSJbawLPNddZavNwkb9SrThmGi
source ../../../../.newenv/bin/activate
python3 manage.py runserver 0.0.0.0:8080
