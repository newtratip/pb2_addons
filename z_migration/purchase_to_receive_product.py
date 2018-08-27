"""
This method will click button receive product in purchase order
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
picking_model = connection.get_model('stock.picking')
acceptance_model = connection.get_model('purchase.work.acceptance')
transfer_details_model = connection.get_model('stock.transfer_details')

# domain follow state
# dom = [('order_type', '=', 'purchase_order'), ('state', '=', 'confirmed')]

# domain follow purchase id
dom = [('order_type', '=', 'purchase_order'),
       ('id', 'in', [1200])]

# Search puchase by domain as defined
pos = po_model.search_read(dom)

pass_po_ids, pass_po_names = [], []
error_po_ids, error_po_names = [], []
for po in pos:
    try:
        for picking_id in po['picking_ids']:
            picking = picking_model.search_read(
                [('id', '=', picking_id)])[0]
            # Save Work Acceptance
            dom_acceptance = [
                ('state', 'not in', ('done', 'cancel')),
                ('order_id', '=',
                 picking_model.search_read(
                    [('id', '=', picking_id)])[0]['origin'])]
            acceptance_ids = acceptance_model.search(dom_acceptance)
            if acceptance_ids:
                picking_model.write(
                    [picking_id], {'acceptance_id': acceptance_ids[0]})
            detail_id = \
                picking_model.do_enter_transfer_details([picking_id])['res_id']
            transfer_details_model.do_detailed_transfer(detail_id)
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
