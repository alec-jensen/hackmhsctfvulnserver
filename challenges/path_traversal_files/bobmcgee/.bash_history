cd ~/web/files
ls -la
nano todo.txt
git status
git add .
git commit -m "Updated TODO list"
git push origin main
cd ~/Videos
ls
rm 2025-02-02.mp4
cd ~/.ssh
cat id_rsa
ssh-add id_rsa
cd ~/web/files
python3 server.py
curl http://localhost:8080/file-access/file?filename=notes.txt
curl http://localhost:8080/file-access/file?filename=contacts.csv
exit
