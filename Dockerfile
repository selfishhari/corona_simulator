FROM  lppier/docker-prophet
EXPOSE 8501
WORKDIR /app
COPY requirements_docker.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
# Install Chrome
COPY chrome_install.sh /tmp
RUN chmod +x /tmp/chrome_install.sh
RUN /tmp/chrome_install.sh
COPY . .
CMD streamlit run corona-calculator.py
