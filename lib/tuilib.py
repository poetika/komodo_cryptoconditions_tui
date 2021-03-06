from lib import rpclib
import json
import time
import readline
import re
import sys
import pickle
import platform
import os
from slickrpc import Proxy
from binascii import hexlify
from binascii import unhexlify
from functools import partial



def colorize(string, color):

    colors = {
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'green': '\033[92m',
        'red': '\033[91m'
    }
    if color not in colors:
        return string
    else:
        return colors[color] + string + '\033[0m'


def rpc_connection_tui():
    # TODO: possible to save multiply entries from successfull sessions and ask user to choose then
    while True:
        restore_choice = input("Do you want to use connection details from previous session? [y/n]: ")
        if restore_choice == "y":
            try:
                with open("connection.json", "r") as file:
                    connection_json = json.load(file)
                    rpc_user = connection_json["rpc_user"]
                    rpc_password = connection_json["rpc_password"]
                    rpc_port = connection_json["rpc_port"]
                    rpc_connection = rpclib.rpc_connect(rpc_user, rpc_password, int(rpc_port))
            except FileNotFoundError:
                print(colorize("You do not have cached connection details. Please select n for connection setup", "red"))
            break
        elif restore_choice == "n":
            rpc_user = input("Input your rpc user: ")
            rpc_password = input("Input your rpc password: ")
            rpc_port = input("Input your rpc port: ")
            connection_details = {"rpc_user": rpc_user,
                                  "rpc_password": rpc_password,
                                  "rpc_port": rpc_port}
            connection_json = json.dumps(connection_details)
            with open("connection.json", "w+") as file:
                file.write(connection_json)
            rpc_connection = rpclib.rpc_connect(rpc_user, rpc_password, int(rpc_port))
            break
        else:
            print(colorize("Please input y or n", "red"))
    return rpc_connection


def def_credentials(chain):
    rpcport ='';
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Win64':
        ac_dir = "dont have windows machine now to test"
    if chain == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + chain + '/' + chain + '.conf')
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpcuser = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpcpassword = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpcport = l.replace('rpcport=', '')
    if len(rpcport) == 0:
        if chain == 'KMD':
            rpcport = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check "+coin_config_file)
            exit(1)

    return(Proxy("http://%s:%s@127.0.0.1:%d"%(rpcuser, rpcpassword, int(rpcport))))


def getinfo_tui(rpc_connection):

    info_raw = rpclib.getinfo(rpc_connection)
    if isinstance(info_raw, dict):
        for key in info_raw:
            print("{}: {}".format(key, info_raw[key]))
        input("Press [Enter] to continue...")
    else:
        print("Error!\n")
        print(info_raw)
        input("\nPress [Enter] to continue...")


def token_create_tui(rpc_connection):

    while True:
        try:
            name = input("Set your token name: ")
            supply = input("Set your token supply: ")
            description = input("Set your token description: ")
        except KeyboardInterrupt:
            break
        else:
            token_hex = rpclib.token_create(rpc_connection, name, supply, description)
        if token_hex['result'] == "error":
            print(colorize("\nSomething went wrong!\n", "pink"))
            print(token_hex)
            print("\n")
            input("Press [Enter] to continue...")
            break
        else:
            try:
                token_txid = rpclib.sendrawtransaction(rpc_connection,
                                                       token_hex['hex'])
            except KeyError:
                print(token_txid)
                print("Error")
                input("Press [Enter] to continue...")
                break
            finally:
                print(colorize("Token creation transaction broadcasted: " + token_txid, "green"))
                file = open("tokens_list", "a")
                file.writelines(token_txid + "\n")
                file.close()
                print(colorize("Entry added to tokens_list file!\n", "green"))
                input("Press [Enter] to continue...")
                break


def oracle_create_tui(rpc_connection):

    print(colorize("\nAvailiable data types:\n", "blue"))
    oracles_data_types = ["Ihh -> height, blockhash, merkleroot\ns -> <256 char string\nS -> <65536 char string\nd -> <256 binary data\nD -> <65536 binary data",
                "c -> 1 byte signed little endian number, C unsigned\nt -> 2 byte signed little endian number, T unsigned",
                "i -> 4 byte signed little endian number, I unsigned\nl -> 8 byte signed little endian number, L unsigned",
                "h -> 32 byte hash\n"]
    for oracles_type in oracles_data_types:
        print(str(oracles_type))
    while True:
        try:
            name = input("Set your oracle name: ")
            description = input("Set your oracle description: ")
            oracle_data_type = input("Set your oracle type (e.g. Ihh): ")
        except KeyboardInterrupt:
            break
        else:
            oracle_hex = rpclib.oracles_create(rpc_connection, name, description, oracle_data_type)
        if oracle_hex['result'] == "error":
            print(colorize("\nSomething went wrong!\n", "pink"))
            print(oracle_hex)
            print("\n")
            input("Press [Enter] to continue...")
            break
        else:
            try:
                oracle_txid = rpclib.sendrawtransaction(rpc_connection, oracle_hex['hex'])
            except KeyError:
                print(oracle_txid)
                print("Error")
                input("Press [Enter] to continue...")
                break
            finally:
                print(colorize("Oracle creation transaction broadcasted: " + oracle_txid, "green"))
                file = open("oracles_list", "a")
                file.writelines(oracle_txid + "\n")
                file.close()
                print(colorize("Entry added to oracles_list file!\n", "green"))
                input("Press [Enter] to continue...")
                break


def oracle_register_tui(rpc_connection):
    #TODO: have an idea since blackjoker new RPC call
    #grab all list and printout only or which owner match with node pubkey
    try:
        print(colorize("Oracles created from this instance by TUI: \n", "blue"))
        with open("oracles_list", "r") as file:
            for oracle in file:
                print(oracle)
        print(colorize('_' * 65, "blue"))
        print("\n")
    except FileNotFoundError:
        print("Seems like a no oracles created from this instance yet\n")
        pass
    while True:
        try:
            oracle_id = input("Input txid of oracle you want to register to: ")
            data_fee = input("Set publisher datafee (in satoshis): ")
        except KeyboardInterrupt:
            break
        oracle_register_hex = rpclib.oracles_register(rpc_connection, oracle_id, data_fee)
        if oracle_register_hex['result'] == "error":
            print(colorize("\nSomething went wrong!\n", "pink"))
            print(oracle_register_hex)
            print("\n")
            input("Press [Enter] to continue...")
            break
        else:
            try:
                oracle_register_txid = rpclib.sendrawtransaction(rpc_connection, oracle_register_hex['hex'])
            except KeyError:
                print(oracle_register_hex)
                print("Error")
                input("Press [Enter] to continue...")
                break
            else:
                print(colorize("Oracle registration transaction broadcasted: " + oracle_register_txid, "green"))
                input("Press [Enter] to continue...")
                break


def oracle_subscription_utxogen(rpc_connection):
    # TODO: have an idea since blackjoker new RPC call
    # grab all list and printout only or which owner match with node pubkey
    try:
        print(colorize("Oracles created from this instance by TUI: \n", "blue"))
        with open("oracles_list", "r") as file:
            for oracle in file:
                print(oracle)
        print(colorize('_' * 65, "blue"))
        print("\n")
    except FileNotFoundError:
        print("Seems like a no oracles created from this instance yet\n")
        pass
    while True:
        try:
            oracle_id = input("Input oracle ID you want to subscribe to: ")
            #printout to fast copypaste publisher id
            oracle_info = rpclib.oracles_info(rpc_connection, oracle_id)
            publishers = 0
            print(colorize("\nPublishers registered for a selected oracle: \n", "blue"))
            try:
                for entry in oracle_info["registered"]:
                    publisher = entry["publisher"]
                    print(publisher + "\n")
                    publishers = publishers + 1
                print("Total publishers:{}".format(publishers))
            except (KeyError, ConnectionResetError):
                print(colorize("Please re-check your input. Oracle txid seems not valid.", "red"))
                pass
            print(colorize('_' * 65, "blue"))
            print("\n")
            if publishers == 0:
                print(colorize("This oracle have no publishers to subscribe.\n"
                               "Please register as an oracle publisher first and/or wait since registration transaciton mined!", "red"))
                input("Press [Enter] to continue...")
                break
            publisher_id = input("Input oracle publisher id you want to subscribe to: ")
            data_fee = input("Input subscription fee (in COINS!): ")
            utxo_num = int(input("Input how many transactions you want to broadcast: "))
        except KeyboardInterrupt:
            break
        while utxo_num > 0:
            while True:
                oracle_subscription_hex = rpclib.oracles_subscribe(rpc_connection, oracle_id, publisher_id, data_fee)
                oracle_subscription_txid = rpclib.sendrawtransaction(rpc_connection, oracle_subscription_hex['hex'])
                mempool = rpclib.get_rawmempool(rpc_connection)
                if oracle_subscription_txid in mempool:
                    break
                else:
                    pass
            print(colorize("Oracle subscription transaction broadcasted: " + oracle_subscription_txid, "green"))
            utxo_num = utxo_num - 1
        input("Press [Enter] to continue...")
        break

def gateways_bind_tui(rpc_connection):
    # main loop with keyboard interrupt handling
    while True:
        try:
            while True:
                try:
                    print(colorize("Tokens created from this instance by TUI: \n", "blue"))
                    with open("tokens_list", "r") as file:
                        for oracle in file:
                            print(oracle)
                    print(colorize('_' * 65, "blue"))
                    print("\n")
                except FileNotFoundError:
                    print("Seems like a no oracles created from this instance yet\n")
                    pass
                token_id = input("Input id of token you want to use in gw bind: ")
                try:
                    token_name = rpclib.token_info(rpc_connection, token_id)["name"]
                except KeyError:
                    print(colorize("Not valid tokenid. Please try again.", "red"))
                    input("Press [Enter] to continue...")
                token_info = rpclib.token_info(rpc_connection, token_id)
                print(colorize("\n{} token total supply: {}\n".format(token_id, token_info["supply"]), "blue"))
                token_supply = input("Input supply for token binding: ")
                try:
                    print(colorize("\nOracles created from this instance by TUI: \n", "blue"))
                    with open("oracles_list", "r") as file:
                        for oracle in file:
                            print(oracle)
                    print(colorize('_' * 65, "blue"))
                    print("\n")
                except FileNotFoundError:
                    print("Seems like a no oracles created from this instance yet\n")
                    pass
                oracle_id = input("Input id of oracle you want to use in gw bind: ")
                try:
                    oracle_name = rpclib.oracles_info(rpc_connection, oracle_id)["name"]
                except KeyError:
                    print(colorize("Not valid oracleid. Please try again.", "red"))
                    input("Press [Enter] to continue...")
                while True:
                    coin_name = input("Input external coin ticker (binded oracle and token need to have same name!): ")
                    if token_name == oracle_name and token_name == coin_name:
                        break
                    else:
                        print(colorize("Token name, oracle name and external coin ticker should match!", "red"))
                while True:
                    M = input("Input minimal amount of pubkeys needed for transaction confirmation (1 for non-multisig gw): ")
                    N = input("Input maximal amount of pubkeys needed for transaction confirmation (1 for non-multisig gw): ")
                    if (int(N) >= int(M)):
                        break
                    else:
                        print("Maximal amount of pubkeys should be more or equal than minimal. Please try again.")
                pubkeys = []
                for i in range(int(N)):
                    pubkeys.append(input("Input pubkey {}: ".format(i+1)))
                #pubkeys = ', '.join(pubkeys)
                args = [rpc_connection, token_id, oracle_id, coin_name, token_supply, M, N]
                args = args + pubkeys
                # broadcasting block
                try:
                    gateways_bind_hex = rpclib.gateways_bind(*args)
                except Exception as e:
                    print(e)
                    input("Press [Enter] to continue...")
                    break
                try:
                    gateways_bind_txid = rpclib.sendrawtransaction(rpc_connection, gateways_bind_hex["hex"])
                except Exception as e:
                    print(e)
                    print(gateways_bind_hex)
                    input("Press [Enter] to continue...")
                    break
                else:
                    print(colorize("Gateway bind transaction broadcasted: " + gateways_bind_txid, "green"))
                    file = open("gateways_list", "a")
                    file.writelines(gateways_bind_txid + "\n")
                    file.close()
                    print(colorize("Entry added to gateways_list file!\n", "green"))
                    input("Press [Enter] to continue...")
                    break
            break
        except KeyboardInterrupt:
            break

# temporary :trollface: custom connection function solution
# to have connection to KMD daemon and cache it in separate file


def rpc_kmd_connection_tui():
    while True:
        restore_choice = input("Do you want to use KMD daemon connection details from previous session? [y/n]: ")
        if restore_choice == "y":
            try:
                with open("connection_kmd.json", "r") as file:
                    connection_json = json.load(file)
                    rpc_user = connection_json["rpc_user"]
                    rpc_password = connection_json["rpc_password"]
                    rpc_port = connection_json["rpc_port"]
                    rpc_connection_kmd = rpclib.rpc_connect(rpc_user, rpc_password, int(rpc_port))
                    try:
                        print(rpc_connection_kmd.getinfo())
                        print(colorize("Successfully connected!\n", "green"))
                        input("Press [Enter] to continue...")
                        break
                    except Exception as e:
                        print(e)
                        print(colorize("NOT CONNECTED!\n", "red"))
                        input("Press [Enter] to continue...")
                        break
            except FileNotFoundError:
                print(colorize("You do not have cached KMD daemon connection details."
                               " Please select n for connection setup", "red"))
                input("Press [Enter] to continue...")
        elif restore_choice == "n":
            rpc_user = input("Input your rpc user: ")
            rpc_password = input("Input your rpc password: ")
            rpc_port = input("Input your rpc port: ")
            connection_details = {"rpc_user": rpc_user,
                                  "rpc_password": rpc_password,
                                  "rpc_port": rpc_port}
            connection_json = json.dumps(connection_details)
            with open("connection_kmd.json", "w+") as file:
                file.write(connection_json)
            rpc_connection_kmd = rpclib.rpc_connect(rpc_user, rpc_password, int(rpc_port))
            try:
                print(rpc_connection_kmd.getinfo())
                print(colorize("Successfully connected!\n", "green"))
                input("Press [Enter] to continue...")
                break
            except Exception as e:
                print(e)
                print(colorize("NOT CONNECTED!\n", "red"))
                input("Press [Enter] to continue...")
                break
        else:
            print(colorize("Please input y or n", "red"))
    return rpc_connection_kmd


def z_sendmany_twoaddresses(rpc_connection, sendaddress, recepient1, amount1, recepient2, amount2):
    str_sending_block = "[{{\"address\":\"{}\",\"amount\":{}}},{{\"address\":\"{}\",\"amount\":{}}}]".format(recepient1, amount1, recepient2, amount2)
    sending_block = json.loads(str_sending_block)
    operation_id = rpc_connection.z_sendmany(sendaddress,sending_block)
    return operation_id


def operationstatus_to_txid(rpc_connection, zstatus):
    str_sending_block = "[\"{}\"]".format(zstatus)
    sending_block = json.loads(str_sending_block)
    operation_json = rpc_connection.z_getoperationstatus(sending_block)
    operation_dump = json.dumps(operation_json)
    operation_dict = json.loads(operation_dump)[0]
    txid = operation_dict['result']['txid']
    return txid


def gateways_send_kmd(rpc_connection):
     # TODO: have to handle CTRL+C on text input
     print(colorize("Please be carefull when input wallet addresses and amounts since all transactions doing in real KMD!", "pink"))
     print("Your addresses with balances: ")
     list_address_groupings = rpc_connection.listaddressgroupings()
     for address in list_address_groupings:
         print(str(address) + "\n")
     sendaddress = input("Input address from which you transfer KMD: ")
     recepient1 = input("Input address which belongs to pubkey which will receive tokens: ")
     amount1 = 0.0001
     recepient2 = input("Input gateway deposit address: ")
     file = open("deposits_list", "a")
     #have to show here deposit addresses for gateways created by user
     amount2 = input("Input how many KMD you want to deposit on this gateway: ")
     operation = z_sendmany_twoaddresses(rpc_connection, sendaddress, recepient1, amount1, recepient2, amount2)
     print("Operation proceed! " + str(operation) + " Let's wait 2 seconds to get txid")
     # trying to avoid pending status of operation
     time.sleep(2)
     txid = operationstatus_to_txid(rpc_connection, operation)
     file.writelines(txid + "\n")
     file.close()
     print(colorize("KMD Transaction ID: " + str(txid) + " Entry added to deposits_list file", "green"))
     input("Press [Enter] to continue...")


def gateways_deposit_tui(rpc_connection_assetchain, rpc_connection_komodo):
    while True:
        bind_txid = input("Input your gateway bind txid: ")
        coin_name = input("Input your external coin ticker (e.g. KMD): ")
        coin_txid = input("Input your deposit txid: ")
        dest_pub = input("Input pubkey which claim deposit: ")
        amount = input("Input amount of your deposit: ")
        height = rpc_connection_komodo.getrawtransaction(coin_txid, 1)["height"]
        deposit_hex = rpc_connection_komodo.getrawtransaction(coin_txid, 1)["hex"]
        claim_vout = "0"
        proof_sending_block = "[\"{}\"]".format(coin_txid)
        proof = rpc_connection_komodo.gettxoutproof(json.loads(proof_sending_block))
        # !!! height needs to be converted to string, omegalul
        deposit_hex = rpclib.gateways_deposit(rpc_connection_assetchain, bind_txid, str(height), coin_name, \
                         coin_txid, claim_vout, deposit_hex, proof, dest_pub, amount)
        deposit_txid = rpclib.sendrawtransaction(rpc_connection_assetchain, deposit_hex["hex"])
        print("Done! Gateways deposit txid is: " + deposit_txid + " Please not forget to claim your deposit!")
        input("Press [Enter] to continue...")
        break


def gateways_claim_tui(rpc_connection):
    while True:
        bind_txid = input("Input your gateway bind txid: ")
        coin_name = input("Input your external coin ticker (e.g. KMD): ")
        deposit_txid = input("Input your gatewaysdeposit txid: ")
        dest_pub = input("Input pubkey which claim deposit: ")
        amount = input("Input amount of your deposit: ")
        claim_hex = rpclib.gateways_claim(rpc_connection, bind_txid, coin_name, deposit_txid, dest_pub, amount)
        try:
            claim_txid = rpclib.sendrawtransaction(rpc_connection, claim_hex["hex"])
        except Exception as e:
            print(e)
            print(claim_hex)
            input("Press [Enter] to continue...")
            break
        else:
            print("Succesfully claimed! Claim transaction id: " + claim_txid)
            input("Press [Enter] to continue...")
            break


def gateways_withdrawal_tui(rpc_connection):
    while True:
        bind_txid = input("Input your gateway bind txid: ")
        coin_name = input("Input your external coin ticker (e.g. KMD): ")
        withdraw_pub = input("Input pubkey to which you want to withdraw: ")
        amount = input("Input amount of withdrawal: ")
        withdraw_hex = rpclib.gateways_withdraw(rpc_connection, bind_txid, coin_name, withdraw_pub, amount)
        withdraw_txid = rpclib.sendrawtransaction(rpc_connection, withdraw_hex["hex"])
        print(withdraw_txid)
        input("Press [Enter] to continue...")
        break


def print_mempool(rpc_connection):
    while True:
        mempool = rpclib.get_rawmempool(rpc_connection)
        tx_counter = 0
        print(colorize("Transactions in mempool: \n", "magenta"))
        for transaction in mempool:
            print(transaction + "\n")
            tx_counter = tx_counter + 1
        print("Total: " + str(tx_counter) + " transactions\n")
        print("R + Enter to refresh list. E + Enter to exit menu." + "\n")
        is_refresh = input("Choose your destiny: ")
        if is_refresh == "R":
            print("\n")
            pass
        elif is_refresh == "E":
            print("\n")
            break
        else:
            print("\nPlease choose R or E\n")


def print_tokens_list(rpc_connection):
    # TODO: have to print it with tokeninfo to have sense
    pass


def print_tokens_balances(rpc_connection):
    # TODO: checking tokenbalance for each token from tokenlist and reflect non zero ones
    pass


def hexdump(filename, chunk_size=1<<15):
    data = ""
    #add_spaces = partial(re.compile(b'(..)').sub, br'\1 ')
    #write = getattr(sys.stdout, 'buffer', sys.stdout).write
    with open(filename, 'rb') as file:
        for chunk in iter(partial(file.read, chunk_size), b''):
            data += str(hexlify(chunk).decode())
    return data


def convert_file_oracle_d(rpc_connection):
    while True:
        path = input("Input path to file you want to upload to oracle: ")
        try:
            hex_data = (hexdump(path, 1))[2:]
        except Exception as e:
            print(e)
            print("Seems something goes wrong (I guess you've specified wrong path)!")
            input("Press [Enter] to continue...")
            break
        else:
            length = round(len(hex_data) / 2)
            if length > 256:
                print("Length: " + str(length) + " bytes")
                print("File is too big for this app")
                input("Press [Enter] to continue...")
                break
            else:
                hex_length = format(length, '#04x')[2:]
                data_for_oracle = str(hex_length) + hex_data
                print("File hex representation: \n")
                print(data_for_oracle + "\n")
                print("Length: " + str(length) + " bytes")
                print("File converted!")
                new_oracle_hex = rpclib.oracles_create(rpc_connection, "tonyconvert", path, "d")
                new_oracle_txid = rpclib.sendrawtransaction(rpc_connection, new_oracle_hex["hex"])
                time.sleep(0.5)
                oracle_register_hex = rpclib.oracles_register(rpc_connection, new_oracle_txid, "10000")
                oracle_register_txid = rpclib.sendrawtransaction(rpc_connection, oracle_register_hex["hex"])
                time.sleep(0.5)
                oracle_subscribe_hex = rpclib.oracles_subscribe(rpc_connection, new_oracle_txid, rpclib.getinfo(rpc_connection)["pubkey"], "0.001")
                oracle_subscribe_txid = rpclib.sendrawtransaction(rpc_connection, oracle_subscribe_hex["hex"])
                time.sleep(0.5)
                while True:
                    mempool = rpclib.get_rawmempool(rpc_connection)
                    if oracle_subscribe_txid in mempool:
                        print("Waiting for oracle subscribtion tx to be mined" + "\n")
                        time.sleep(6)
                        pass
                    else:
                        break
                oracles_data_hex = rpclib.oracles_data(rpc_connection, new_oracle_txid, data_for_oracle)
                try:
                    oracle_data_txid = rpclib.sendrawtransaction(rpc_connection, oracles_data_hex["hex"])
                except Exception as e:
                    print(oracles_data_hex)
                    print(e)
                print("Oracle created: " + str(new_oracle_txid))
                print("Data published: " + str(oracle_data_txid))
                input("Press [Enter] to continue...")
                break


def convert_file_oracle_D(rpc_connection):
    while True:
        path = input("Input path to file you want to upload to oracle: ")
        try:
            hex_data = (hexdump(path, 1))
        except Exception as e:
            print(e)
            print("Seems something goes wrong (I guess you've specified wrong path)!")
            input("Press [Enter] to continue...")
            break
        else:
            length = round(len(hex_data) / 2)
            # if length > 800000:
            #     print("Too big file size to upload for this version of program. Maximum size is 800KB.")
            #     input("Press [Enter] to continue...")
            #     break
            if length > 8000:
                # if file is more than 8000 bytes - slicing it to <= 8000 bytes chunks (16000 symbols = 8000 bytes)
                data = [hex_data[i:i + 16000] for i in range(0, len(hex_data), 16000)]
                chunks_amount = len(data)
                # TODO: have to create oracle but subscribe this time chunks amount times to send whole file in same block
                # TODO: 2 - on some point file will not fit block - have to find this point
                # TODO: 3 way how I want to implement it first will keep whole file in RAM - have to implement some way to stream chunks to oracle before whole file readed
                # TODO: have to "optimise" registration fee
                # Maybe just check size first by something like a du ?
                print("Length: " + str(length) + " bytes.\n Chunks amount: " + str(chunks_amount))
                new_oracle_hex = rpclib.oracles_create(rpc_connection, "tonyconvert_" + str(chunks_amount), path, "D")
                new_oracle_txid = rpclib.sendrawtransaction(rpc_connection, new_oracle_hex["hex"])
                time.sleep(0.5)
                oracle_register_hex = rpclib.oracles_register(rpc_connection, new_oracle_txid, "10000")
                oracle_register_txid = rpclib.sendrawtransaction(rpc_connection, oracle_register_hex["hex"])
                # subscribe chunks_amount + 1 times, but lets limit our broadcasting 100 tx per block (800KB/block)
                if chunks_amount > 100:
                    utxo_num = 101
                else:
                    utxo_num = chunks_amount
                while utxo_num > 0:
                    while True:
                        oracle_subscription_hex = rpclib.oracles_subscribe(rpc_connection, new_oracle_txid, rpclib.getinfo(rpc_connection)["pubkey"], "0.001")
                        oracle_subscription_txid = rpclib.sendrawtransaction(rpc_connection,
                                                                             oracle_subscription_hex['hex'])
                        mempool = rpclib.get_rawmempool(rpc_connection)
                        if oracle_subscription_txid in mempool:
                            break
                        else:
                            pass
                    print(colorize("Oracle subscription transaction broadcasted: " + oracle_subscription_txid, "green"))
                    utxo_num = utxo_num - 1
                # waiting for last broadcasted subscribtion transaction to be mined to be sure that money are on oracle balance
                while True:
                    mempool = rpclib.get_rawmempool(rpc_connection)
                    if oracle_subscription_txid in mempool:
                        print("Waiting for oracle subscribtion tx to be mined" + "\n")
                        time.sleep(6)
                        pass
                    else:
                        break
                print("Oracle preparation is finished. Oracle txid: " + new_oracle_txid)
                # can publish data now
                counter = 0
                for chunk in data:
                    hex_length_bigendian = format(round(len(chunk) / 2), '#06x')[2:]
                    # swap to get little endian length
                    a = hex_length_bigendian[2:]
                    b = hex_length_bigendian[:2]
                    hex_length = a + b
                    data_for_oracle = str(hex_length) + chunk
                    counter = counter + 1
                    # print("Chunk number: " + str(counter) + "\n")
                    # print(data_for_oracle)
                    try:
                        oracles_data_hex = rpclib.oracles_data(rpc_connection, new_oracle_txid, data_for_oracle)
                    except Exception as e:
                        print(data_for_oracle)
                        print(e)
                        input("Press [Enter] to continue...")
                        break
                    # on broadcasting ensuring that previous one reached mempool before blast next one
                    while True:
                        mempool = rpclib.get_rawmempool(rpc_connection)
                        oracle_data_txid = rpclib.sendrawtransaction(rpc_connection, oracles_data_hex["hex"])
                        #time.sleep(0.1)
                        if oracle_data_txid in mempool:
                            break
                        else:
                            pass
                    # blasting not more than 100 at once (so maximum capacity per block can be changed here)
                    # but keep in mind that registration UTXOs amount needs to be changed too !
                    if counter % 100 == 0 and chunks_amount > 100:
                        while True:
                            mempool = rpclib.get_rawmempool(rpc_connection)
                            if oracle_data_txid in mempool:
                                print("Waiting for previous data chunks to be mined before send new ones" + "\n")
                                print("Sent " + str(counter) + " chunks from " + str(chunks_amount))
                                time.sleep(6)
                                pass
                            else:
                                break

                print("Last baton: " + oracle_data_txid)
                input("Press [Enter] to continue...")
                break
            # if file suits single oraclesdata just broadcasting it straight without any slicing
            else:
                hex_length_bigendian = format(length, '#06x')[2:]
                # swap to get little endian length
                a = hex_length_bigendian[2:]
                b = hex_length_bigendian[:2]
                hex_length = a + b
                data_for_oracle = str(hex_length) + hex_data
                print("File hex representation: \n")
                print(data_for_oracle + "\n")
                print("Length: " + str(length) + " bytes")
                print("File converted!")
                new_oracle_hex = rpclib.oracles_create(rpc_connection, "tonyconvert_" + "1", path, "D")
                new_oracle_txid = rpclib.sendrawtransaction(rpc_connection, new_oracle_hex["hex"])
                time.sleep(0.5)
                oracle_register_hex = rpclib.oracles_register(rpc_connection, new_oracle_txid, "10000")
                oracle_register_txid = rpclib.sendrawtransaction(rpc_connection, oracle_register_hex["hex"])
                time.sleep(0.5)
                oracle_subscribe_hex = rpclib.oracles_subscribe(rpc_connection, new_oracle_txid, rpclib.getinfo(rpc_connection)["pubkey"], "0.001")
                oracle_subscribe_txid = rpclib.sendrawtransaction(rpc_connection, oracle_subscribe_hex["hex"])
                time.sleep(0.5)
                while True:
                    mempool = rpclib.get_rawmempool(rpc_connection)
                    if oracle_subscribe_txid in mempool:
                        print("Waiting for oracle subscribtion tx to be mined" + "\n")
                        time.sleep(6)
                        pass
                    else:
                        break
                oracles_data_hex = rpclib.oracles_data(rpc_connection, new_oracle_txid, data_for_oracle)
                try:
                    oracle_data_txid = rpclib.sendrawtransaction(rpc_connection, oracles_data_hex["hex"])
                except Exception as e:
                    print(oracles_data_hex)
                    print(e)
                    input("Press [Enter] to continue...")
                    break
                else:
                    print("Oracle created: " + str(new_oracle_txid))
                    print("Data published: " + str(oracle_data_txid))
                    input("Press [Enter] to continue...")
                    break


def get_files_list(rpc_connection):

    start_time = time.time()
    oracles_list = rpclib.oracles_list(rpc_connection)
    files_list = []
    for oracle_txid in oracles_list:
        oraclesinfo_result = rpclib.oracles_info(rpc_connection, oracle_txid)
        description = oraclesinfo_result['description']
        name = oraclesinfo_result['name']
        if name[0:12] == 'tonyconvert_':
            new_file = '[' + name + ': ' + description + ']: ' + oracle_txid
            files_list.append(new_file)
    print("--- %s seconds ---" % (time.time() - start_time))
    return files_list


def display_files_list(rpc_connection):
    print("Scanning oracles. Please wait...")
    list_to_display = get_files_list(rpc_connection)
    while True:
        for file in list_to_display:
            print(file + "\n")
        input("Press [Enter] to continue...")
        break


def files_downloader(rpc_connection):
    while True:
        display_files_list(rpc_connection)
        print("\n")
        oracle_id = input("Input oracle ID you want to download file from: ")
        output_path = input("Input output path for downloaded file (name included) e.g. /home/test.txt: ")
        oracle_info = rpclib.oracles_info(rpc_connection, oracle_id)
        name = oracle_info['name']
        latest_baton_txid = oracle_info['registered'][0]['batontxid']
        if name[0:12] == 'tonyconvert_':
            # downloading process here
            chunks_amount = int(name[12:])
            data = rpclib.oracles_samples(rpc_connection, oracle_id, latest_baton_txid, str(chunks_amount))["samples"]
            for chunk in reversed(data):
                with open(output_path, 'ab+') as file:
                    file.write(unhexlify(chunk[0]))
            print("I hope that file saved to " + output_path + "\n")
            input("Press [Enter] to continue...")
            break

        else:
            print("I cant recognize file inside this oracle. I'm very sorry, boss.")
            input("Press [Enter] to continue...")
            break


def marmara_receive_tui(rpc_connection):
    while True:
        issuer_pubkey = input("Input pubkey of person who do you want to receive MARMARA from: ")
        issuance_sum = input("Input amount of MARMARA you want to receive: ")
        blocks_valid = input("Input amount of blocks for cheque matures: ")
        try:
            marmara_receive_txinfo = rpc_connection.marmarareceive(issuer_pubkey, issuance_sum, "MARMARA", blocks_valid)
            marmara_receive_txid = rpc_connection.sendrawtransaction(marmara_receive_txinfo["hex"])
            print("Marmara receive txid broadcasted: " + marmara_receive_txid + "\n")
            print(json.dumps(marmara_receive_txinfo, indent=4, sort_keys=True) + "\n")
            with open("receive_txids.txt", 'a+') as file:
                file.write(marmara_receive_txid + "\n")
                file.write(json.dumps(marmara_receive_txinfo, indent=4, sort_keys=True) + "\n")
            print("Transaction id is saved to receive_txids.txt file.")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(marmara_receive_txinfo)
            print(e)
            print("Something went wrong. Please check your input")


def marmara_issue_tui(rpc_connection):
    while True:
        receiver_pubkey = input("Input pubkey of person who do you want to issue MARMARA: ")
        issuance_sum = input("Input amount of MARMARA you want to issue: ")
        maturing_block = input("Input number of block on which issuance mature: ")
        approval_txid = input("Input receiving request transaction id: ")
        try:
            marmara_issue_txinfo = rpc_connection.marmaraissue(receiver_pubkey, issuance_sum, "MARMARA", maturing_block, approval_txid)
            marmara_issue_txid = rpc_connection.sendrawtransaction(marmara_issue_txinfo["hex"])
            print("Marmara issuance txid broadcasted: " + marmara_issue_txid + "\n")
            print(json.dumps(marmara_issue_txinfo, indent=4, sort_keys=True) + "\n")
            with open("issue_txids.txt", "a+") as file:
                file.write(marmara_issue_txid + "\n")
                file.write(json.dumps(marmara_issue_txinfo, indent=4, sort_keys=True) + "\n")
            print("Transaction id is saved to issue_txids.txt file.")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(marmara_issue_txinfo)
            print(e)
            print("Something went wrong. Please check your input")


def marmara_creditloop_tui(rpc_connection):
    while True:
        loop_txid = input("Input transaction ID of credit loop you want to get info about: ")
        try:
            marmara_creditloop_info = rpc_connection.marmaracreditloop(loop_txid)
            print(json.dumps(marmara_creditloop_info, indent=4, sort_keys=True) + "\n")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(marmara_creditloop_info)
            print(e)
            print("Something went wrong. Please check your input")


def marmara_settlement_tui(rpc_connection):
    while True:
        loop_txid = input("Input transaction ID of credit loop to make settlement: ")
        try:
            marmara_settlement_info = rpc_connection.marmarasettlement(loop_txid)
            marmara_settlement_txid = rpc_connection.sendrawtransaction(marmara_settlement_info["hex"])
            print("Loop " + loop_txid + " succesfully settled!\nSettlement txid: " + marmara_settlement_txid)
            with open("settlement_txids.txt", "a+") as file:
                file.write(marmara_settlement_txid + "\n")
                file.write(json.dumps(marmara_settlement_info, indent=4, sort_keys=True) + "\n")
            print("Transaction id is saved to settlement_txids.txt file.")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(marmara_settlement_info)
            print(e)
            print("Something went wrong. Please check your input")
            input("Press [Enter] to continue...")
            break


def marmara_lock_tui(rpc_connection):
    while True:
        amount = input("Input amount of coins you want to lock for settlement and staking: ")
        unlock_height = input("Input height on which coins should be unlocked: ")
        try:
            marmara_lock_info = rpc_connection.marmaralock(amount, unlock_height)
            marmara_lock_txid = rpc_connection.sendrawtransaction(marmara_lock_info["hex"])
            with open("lock_txids.txt", "a+") as file:
                file.write(marmara_lock_txid + "\n")
                file.write(json.dumps(marmara_lock_info, indent=4, sort_keys=True) + "\n")
            print("Transaction id is saved to lock_txids.txt file.")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(e)
            print("Something went wrong. Please check your input")
            input("Press [Enter] to continue...")
            break


def marmara_info_tui(rpc_connection):
    while True:
        firstheight = input("Input first height (default 0): ")
        if not firstheight:
            firstheight = "0"
        lastheight = input("Input last height (default current (0) ): ")
        if not lastheight:
            lastheight = "0"
        minamount = input("Input min amount (default 0): ")
        if not minamount:
            minamount = "0"
        maxamount = input("Input max amount (default 0): ")
        if not maxamount:
            maxamount = "0"
        issuerpk = input("Optional. Input issuer public key: ")
        try:
            if issuerpk:
                marmara_info = rpc_connection.marmarainfo(firstheight, lastheight, minamount, maxamount, "MARMARA", issuerpk)
            else:
                marmara_info = rpc_connection.marmarainfo(firstheight, lastheight, minamount, maxamount)
            print(json.dumps(marmara_info, indent=4, sort_keys=True) + "\n")
            input("Press [Enter] to continue...")
            break
        except Exception as e:
            print(marmara_info)
            print(e)
            print("Something went wrong. Please check your input")
            input("Press [Enter] to continue...")
            break
