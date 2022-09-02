# Importers

<p align="right">
    <img src="https://github.com/simonarvin/eyeloop/blob/master/misc/imgs/importer_overview.svg?raw=true" align="right" height="250">
    </p>

To use a video sequence for eye-tracking, we use an _importer_ class as a bridge to EyeLoop's engine. The source fetches the video sequence from the camera, or offline from a directory, and imports it. Briefly, the source main class `Source` includes functions to rotate, resize and save the video stream. Additionally, it _arms_ the engine by passing neccesary variables.

## Why use an source?

The reason for using an _importer_ class, rather than having video importation "_built-in_", is to avoid incompatibilities. For example, while most web-cameras are compatible with opencv (source _cv_), Vimba-based cameras (Allied Vision cameras), are not. Thus, by modularizing the importation of image frames, EyeLoop is easily integrated in markedly different setups.

## Importers

- Most cameras are compatible with the _cv Importer_ (default).
- Allied Vision cameras require the Vimba-based _Importer_, _vimba_.

## Building your first custom source

To build our first custom source, we instantiate our _Importer_ class:

```python
class Source(Source):
    def __init__(self) -> None:
        self.scale = config.arguments.scale
```

Here, we define critical variables, such as scaling. Then, we load the first frame, retrieve its dimensions and, lastly, _arm_ the engine:

```python
        ...
        (load image)
        width, height = (image dimensions)
        self.arm(width, height, image)
```

Finally, the `route()` function loads the video frames and passes them to the engine sequentially:

```python
def route(self) -> None:
        while True:
            image = ...
            self.on_frame(image) # Callback that will deliver the frame to the engine
            self.frame += 1
```

Optionally, add a `release()` function to control termination of the importation process:

```python
def release(self) -> None:
        terminate()
```

That's it!

> Consider checking out [_cv Importer_](https://github.com/simonarvin/eyeloop/blob/master/importers/cv.py) as a code example.
