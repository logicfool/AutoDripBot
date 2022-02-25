import rich;import builtins;builtins.print = rich.print
from web3 import Web3
import json,os,threading,time
from web3.middleware import geth_poa_middleware

def run_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw,daemon=True)
        t.start()
        return t
    return run

def _get_config():
    """
    Get the configuration from the config file
    """
    if os.path.exists('config.json'):
        with open('config.json') as config_file:
            config = json.load(config_file)
            return config
    else:
        print("[yellow]No config file found creating one....[/yellow]")
        with open('config.json','w') as config_file:
            config = {
                "node_url": "",
                "wallet_privatekeys": ["",""],
            }
            json.dump(config,config_file,indent=4)
            print("[green]Config file created edit and restart![/green]")
            exit()


class DripBot():
    def __init__(self):
        self.config = _get_config()
        if self.config['node_url'] == "":print("[red]No node url found in config file[/red]");exit()
        if "ws" in self.config['node_url']:self.w3 = Web3(Web3.WebsocketProvider(self.config['node_url']))
        else:self.w3 = Web3(Web3.HTTPProvider(self.config['node_url']))
        self._load_wallets()
        self.contract = self._load_contract("drip","0xFFE811714ab35360b67eE195acE7C10D93f89D8C") 
           
    def _load_contract(self,abi_name,address):
        """
        Load the contract from the abi file
        """
        with open(f"assets/{abi_name}.abi") as abi_file:
            abi = json.load(abi_file)
            return self.w3.eth.contract(abi=abi,address=address)
    
    def _load_wallets(self):
        self.wallets = []
        for wallet in self.config['wallet_privatekeys']:
            if wallet=="":continue
            try:self.wallets.append(self.w3.eth.account.privateKeyToAccount(wallet))
            except:print(f"[red]Invalid wallet private key: {wallet}[/red]");
        if len(self.wallets) == 0:print("[red]No valid wallet private key found in config file Exiting...[/red]");exit()
            
    def _get_inputs(self):
        """
        Get the inputs from the user
        """
        inputs = {}
        print("[yellow]Choose an option(1 or 2):[/yellow]\n1. [blue]Auto-Compound[/blue]\n2. [blue]Auto-Claim[/blue]\n")
        try:inputs["option"] = int(input("-> "))
        except :print("[red]Invalid option Please restart and enter properly!! Exiting[/red]");exit()
        print("[yellow]Enter the interval in hours(default:3):[/yellow]\n")
        try:inputs["interval"] = int(input("-> "))
        except :print("[red]You did not enter properly taking 3 hrs by default![/red]");inputs["interval"] = 3
        return inputs
    
    
    def _get_tx_params(self,from_wallet):
        """
        Get the transaction parameters
        """
        nonce = self.w3.eth.getTransactionCount(from_wallet)
        tx = {
            "from":from_wallet,
            "value":0,
            "gasPrice":self.w3.eth.gasPrice,
            "gas":200000,
            "nonce":nonce
        }
        return tx
        
    
    def claim(self):
        """
        Claim the drip
        """
        function = self.contract.functions.claim()
        for ii in self.wallets:
            try:
                tx = function.buildTransaction(self._get_tx_params(ii.address))
                signed = ii.signTransaction(tx)
                self.w3.eth.sendRawTransaction(signed.rawTransaction)
            except:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0);
                tx = function.buildTransaction(self._get_tx_params(ii.address))
                signed = ii.signTransaction(tx)
                self.w3.eth.sendRawTransaction(signed.rawTransaction)
            print(f"[green]Claimed from {ii.address}[/green]")
        
    def auto_compound(self):
        """
        Auto compound the drip
        """
        function = self.contract.functions.roll()
        for ii in self.wallets:
            try:
                tx = function.buildTransaction(self._get_tx_params(ii.address))
                signed = ii.signTransaction(tx)
                self.w3.eth.sendRawTransaction(signed.rawTransaction)
            except:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0);
                tx = function.buildTransaction(self._get_tx_params(ii.address))
                signed = ii.signTransaction(tx)
                self.w3.eth.sendRawTransaction(signed.rawTransaction)
            print(f"[green]Compounded from {ii.address}[/green]")
            
    @run_thread
    def start(self):
        inputs = self._get_inputs()
        interval = int(inputs["interval"])*3600
        while True:
            try:
                if inputs["option"] == 1:self.auto_compound()
                elif inputs["option"] == 2:self.claim()
                print("[green]Sleeping for {} hours[/green]\n".format(inputs["interval"]))
                to_sleep = interval
                while to_sleep>0:
                    to_sleep -= 1
                    print("Time Left: {} Seconds".format(to_sleep),end="\r")
                    time.sleep(1)
                print("[green]Interval Over![/green]")
            except KeyboardInterrupt:
                print("[red]Exiting...[/red]")
                exit()