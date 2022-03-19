//contract address
window.contractAddress = "0x278597679C848E64e8304841505871Ff93bC0B1f";

//file to store the newest contract
window.CONTRACT_FILENAME = "contract.txt";

//contrace abi list
const abi = [
  "function isContractOwner()public view returns(bool)",
  "function getIndexReference() public view returns(string memory)",
  "function setIndexReference(string calldata hash) public onlyOwner returns(bool)"
];


//fetch the newest contrat address
(async function fetchNewestContract(){
  var res = await fetch("https://" + window.location.host + "/contract.txt", {
    "headers": {
      "accept": "application/json, text/plain, */*",
      "accept-language": "zh-CN,zh;q=0.9",
    },
    "method": "GET",
    "credentials": "omit"
  });

  res = await res.json();

  if(res.contract != null && res.contract != undefined && res.contract != ""){
    window.contractAddress = res.contract;
  }
}());

//get the contract engine
function getContract() {
  var contract = new ethers.Contract(window.contractAddress, abi, window.signer);

  return contract;
}

//check if it has connected the metamask or not
function checkConnection() {
  if(window.provider == null || window.provider == undefined){

    disconnect();

    alert("you have not connected to metamask, please click the connect button on the top left!");
    
    return false;
  }  

  return true;
}

//check if contract owner or not
async function isContractOwner(){
  if(!checkConnection()){
    return null;
  }

  var contract = getContract();

  try {

    var res = await contract.isContractOwner();

    return res;

  }catch(e){

    alert(e.stack);

    return null;

  }  
}

//get index reference from smart contract
async function getIndexReference(){
  if(!checkConnection()){
    return null;
  }

  var contract = getContract();

  try {

    var res = await contract.getIndexReference();

    return res;

  }catch(e){

    alert(e.stack);

    return null;

  }
}

//set new index reference to smart contract
async function setIndexReference(hash) {
  if(!checkConnection()){
    return null;
  }

  if(hash == null || hash == undefined){
    alert("index hash is not given!");
    return null;
  }

  if(typeof(hash) != "string"){
    alert("index hash must a string!");
    return null;
  }  

  hash = hash.trim();
  if(hash == ""){
    alert("index hash is empty!")
    return null;
  }

  var contract = getContract();

  try {

    let tx = await contract.setIndexReference(hash);

    await tx.wait();

    return tx.hash;

  } catch(e) {

    alert(e.stack);

    return null;
  
  }
}
