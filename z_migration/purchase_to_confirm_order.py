"""
This method will click button confirm order in purchase order
"""
import openerplib
import ConfigParser
import os

conf = 'migration.conf'


def get_connection(config_file):
    file_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = '%s/%s' % (file_dir, config_file)
    config = ConfigParser.ConfigParser()
    config.readfp(open(file_path))
    hostname = config.get('server', 'hostname')
    port = int(config.get('server', 'port'))
    database = config.get('server', 'database')
    login = config.get('server', 'login')
    password = config.get('server', 'password')
    user_id = int(config.get('server', 'user_id'))
    connection = openerplib.get_connection(
        hostname=hostname, port=port, database=database, login=login,
        password=password, protocol="jsonrpc", user_id=user_id)
    return connection


connection = get_connection(conf)
connection.check_login()

# Start your program ...
po_model = connection.get_model('purchase.order')

# domain follow state
dom = [('order_type', '=', 'purchase_order'), ('state', '=', 'draft')]

# domain follow purchase id
# dom = [('order_type', '=', 'purchase_order'),
#        ('id', 'in', [1200])]

# Search puchase by domain as defined
pos = po_model.search_read(dom)

pass_po_ids, pass_po_names = [], []
error_po_ids, error_po_names = [], []
for po in pos:
    try:
        po_model.signal_workflow([po['id']], 'purchase_confirm')
        pass_po_ids.append(po['id'])
        pass_po_names.append(po['name'])
    except Exception:
        error_po_ids.append(po['id'])
        error_po_names.append(po['name'])

# Show purchase order pass and fail
if pass_po_ids:
    print "=============== Pass ==============="
    print pass_po_ids  # Use for search po id in database
    print pass_po_names  # Use for see number of purchase order as pass
if error_po_ids:
    print "=============== Fail ==============="
    print error_po_ids  # Use for search po id in database
    print error_po_names  # Use for see number of purchase order as fail
