# RankingAnnotator
`RankingAnnotator` is simple annotation server to rank images in order of
preference.
Repeatedly choosing the preferable of 2 images, `RankingAnnotator` generate
image preference ranking.

# Tested environment
* Python 3.9.5
* tornado v6.1
* opencv-python v4.5.1
* SQLAlchemy v1.4.18
* numpy v1.20.3
* nptyping v1.4.2
* Nodejs v14.15.4

# Installation
## Build client
```
    cd client/
    npm install
    npm run build
```

# Start server
To start annotation server on `localhost:8000`,
```
    python server/main.py --input_dir </path/to/image_dir/> --host localhost
    --port 8000
```

# TODO
[] Create image ranking from image preference list.
