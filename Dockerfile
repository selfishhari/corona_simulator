FROM safakcirag/fbprophet
EXPOSE 8501
WORKDIR /app
RUN pip3 install cython
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install
COPY . .
CMD streamlit run corona-calculator.py
