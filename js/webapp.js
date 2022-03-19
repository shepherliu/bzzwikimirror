//user wallet address
window.userAddress = "";

//blockchain id
window.chainId = 0;

//blockchan name
window.chainName = "";

//index file name
window.INDEX_FILENAME = "index";

//connect to the metamask
async function connect() {
  window.provider = new ethers.providers.Web3Provider(window.ethereum);
  // MetaMask requires requesting permission to connect users accounts
  var res = await window.provider.send("eth_requestAccounts", []);

  if(res.length > 0){
    window.userAddress = res[0];

    window.signer = provider.getSigner();

    //detect block chain
    res = await provider.detectNetwork();

    window.chainId = res.chainId;
    window.chainName = res.name;

    if(res.chainId>0&&res.name!=""){

      //change status to connected

      document.getElementById("connect").title = window.userAddress+"("+window.chainName+")";

      document.getElementById("status").innerText = "connected";
      
      refreshWikiPedias();
    } else{
      disconnect();
    }

  }
}

//get wikipedia references from swarm and blockchain, and refresh the website
async function refreshWikiPedias(){

  //get index reference from smart contract
  var reference = await getIndexReference();

  if(reference == null || reference == undefined || reference == ''){
    return;
  }

  //get index items from swarm
  var indexs = await fetchReferenceFromSwarm(reference);
  if(indexs == null || indexs == undefined){
    return;
  }

  //show wiki doc items on website
  renderForIndexs(indexs);
}

//add zim index and make a new index file to swarm, then save the reference to smart contract
async function addReference(hash){
  var isOwner = await isContractOwner();
  if(isOwner == null || isOwner == undefined || isOwner == false){
    alert("only the smart contract owner can add reference!");
    return;
  }

  //get old index reference
  var reference = await getIndexReference();

  if(reference == null || reference == undefined){
    return;
  }

  //get old index items
  var indexs = {};

  if(reference != ''){
    indexs = await fetchReferenceFromSwarm(reference)
    if(indexs == null || indexs == undefined){
      return;
    }
  }

  //get new index items
  var indexForHash = await fetchReferenceFromSwarm(hash)
  if(indexForHash == null || indexForHash == undefined){
    return;
  }

  //add new index items
  indexs[hash] = indexForHash;

  //js-tar file collection
  var data = JSON.stringify(indexs);
  var totalSize = data.length;

  var tar = new Tar();
  tar.append("index", data);

  var metadata = {"name": "index", "size": totalSize,"type":"text"};
  tar.append(window.META_FILE_NAME, JSON.stringify(metadata));

  //save index items to swarm
  var newHash = await uploadReferenceToSwarm(tar.out);
  if(newHash == null || newHash == undefined){
    return;
  }

  //save new index reference to smart contract
  var res = await setIndexReference(newHash);
  if(res == null || res == undefined){
    return;
  }else{
    renderForIndexs(indexs);
  }     
}

//delete zim index and make a new index file to swarm, then save the reference to smart contract
async function delReference(hash){
  var isOwner = await isContractOwner();
  if(isOwner == null || isOwner == undefined || isOwner == false){
    alert("only the smart contract owner can delete reference!");
    return;
  }
   
  //get old index reference  
  var reference = await getIndexReference();

  if(reference == null || reference == undefined || reference == ''){
    return;
  }

  //get old index items
  var indexs = await fetchReferenceFromSwarm(reference)
  if(indexs == null || indexs == undefined){
    return;
  } 

  //delete items for one zim reference
  delete indexs[hash];

  //js-tar file collection
  var data = JSON.stringify(indexs);
  var totalSize = data.length;

  var tar = new Tar();
  tar.append("index", data);

  var metadata = {"name": "index", "size": totalSize, "type":"text"};
  tar.append(window.META_FILE_NAME, JSON.stringify(metadata));

  //save new index items to swarm
  var newHash = await uploadReferenceToSwarm(tar.out);
  if(newHash == null || newHash == undefined){
    return;
  }
  
  //save new index reference to swarm
  var res = await setIndexReference(newHash);
  if(res == null || res == undefined){
    return;
  }else{
    renderForIndexs(indexs);
  }
}

//render the webpage
async function renderForIndexs(indexs){

  window.indexs = indexs;

  await onSearchWiki();

}


//add zim index and make a new index file to swarm, then save the reference to smart contract
async function onAddReference(){
  var reference = prompt("Reference", "");
  if(reference == null || reference == undefined || reference == ''){
    return;
  }

  await addReference(reference);
}

//delete zim index and make a new index file to swarm, then save the reference to smart contract
async function onDeleteReference() {
  var reference = prompt("Reference", "");
  if(reference == null || reference == undefined || reference == ''){
    return;
  } 

  await delReference(reference);
}

//filter wiki doc items
async function onSearchWiki(){

  if(window.indexs == null || window.indexs == undefined){
    return;
  }

  var search = document.getElementById('search').value;

  var html = '<ul id="list">';

  for(var k in window.indexs){
    try{
        for(var v in window.indexs[k]){
        var item = unescape(window.indexs[k][v]);
        if(search == '' || item.indexOf(search) !=-1 ){

          html += '<li style="width:200px;float:left;margin-right:150px;line-height:30px;; word-wrap:break-word; word-break:break-all;"><a></a><a target="_blank" href="' + window.swarmGateway + k +'/A/'+window.indexs[k][v]+'">'+item+'</a><a></a></li><a></a>';

        }
      }
    }catch(e){

    }

  }

  html += '</ul>';
  document.getElementById('messageshows').innerHTML = html;
}