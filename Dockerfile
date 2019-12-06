FROM nikolaik/python-nodejs:latest

RUN pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y git build-essential gcc make yasm autoconf automake cmake libtool libmp3lame-dev pkg-config libunwind-dev zlib1g-dev libssl-dev

RUN apt-get update \
    && apt-get clean \
    && apt-get install -y --no-install-recommends libc6-dev libgdiplus wget software-properties-common

# RUN npm install -g webpack-cli webpack

WORKDIR /usr/src/app

ADD ./package.json /usr/src/app/package.json
RUN yarn install

ADD ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ADD ./webpack.dev.js /usr/src/app/webpack.dev.js
ADD ./webpack.prod.js /usr/src/app/webpack.prod.js
ADD ./public /usr/src/app/public
ADD ./.babelrc /usr/src/app/.babelrc
ADD ./web /usr/src/app/web
RUN yarn build

ADD ./server /usr/src/app/server

ADD ./ /usr/src/app

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "start.py"]
