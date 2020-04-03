FROM python:3.7
EXPOSE 8501
WORKDIR /app
RUN pip3 install cython
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
# Install Chrome
RUN apt-get update && apt-get install -y libnss3-dev
RUN wget -N http://chromedriver.storage.googleapis.com/80.0.3987.16/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN chmod +x chromedriver
RUN mv chromedriver /usr/local/bin
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install
# 80.0.3987.162-1
COPY . .
CMD streamlit run corona-calculator.py
