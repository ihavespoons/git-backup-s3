FROM python:3-slim AS builder
ADD .src/main.py /app
WORKDIR /app

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app boto3

# A distroless container image with Python and some basics like SSL certificates
# https://github.com/GoogleContainerTools/distroless
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app
CMD ["/app/main.py"]