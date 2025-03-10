from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from cz_generation import create_cluster

app = Flask(__name__)

@app.route('/generate-cz')
@cross_origin()
def route_generate_cz():
  try:
    request.get_json(force=True)
  except:
    return jsonify({'message': 'Bad Request'}), 400
  
  if not request.json:
    return jsonify({'message': 'Please specify a CBG, location name, and minimum population'}), 400
  
  cluster, pop = create_cluster(request.json['core_cbg'], request.json['min_pop'])
  
  return jsonify({ 'cluster': cluster, 'population': pop })

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=1738)
