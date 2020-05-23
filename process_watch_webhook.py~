import json
import base64

# Convert Google Pub/Sub webhook into history_id
# history_id reflects most recent Gmail mailbox sequence
def process(request)
	r = request.json
	r_d_encoded = r['message']['data']
	r_d_decoded = base64.b64decode(r_d_encoded.encode('ascii'))
	r_d_decoded = json.loads(r_d_decoded.decode('ascii'))
	history_id = r_d_decoded['historyId']
	return history_id