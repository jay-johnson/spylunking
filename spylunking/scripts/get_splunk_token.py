#!/usr/bin/env python

import spylunking.get_token


token = spylunking.get_token.get_token(
    url="https://localhost:8089")

print(token)
