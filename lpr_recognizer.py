import requests

def recognize_plate(image_path, secret_key):
    with open(image_path, 'rb') as img:
        response = requests.post(
            'https://api.openalpr.com/v3/recognize_bytes',
            params={
                'secret_key': secret_key,
                'recognize_vehicle': 0,
                'country': 'us',
                'return_image': 0
            },
            data=img.read()
        )
    result = response.json()
    if 'results' in result and result['results']:
        plate = result['results'][0]['plate']
        confidence = result['results'][0]['confidence']
        return plate, confidence
    return None, None
