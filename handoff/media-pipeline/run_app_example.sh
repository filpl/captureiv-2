cd /home/user/uplat
export APP_ENV=development PORT=5009 SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))') ADMIN_USERNAME=admin ADMIN_PASSWORD=<set-locally> DATABASE_URL=sqlite:////tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad/audit.db STORAGE_BACKEND=local
exec /tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad/venv/bin/python app.py
