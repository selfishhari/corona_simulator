FROM python:3.7
EXPOSE 8501
WORKDIR /app
RUN pip3 install cython
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
# Install Chromere
COPY chrome_install.sh /tmp
RUN chmod +x /tmp/chrome_install.sh
RUN /tmp/chrome_install.sh
COPY . .
CMD streamlit run corona-calculator.py
