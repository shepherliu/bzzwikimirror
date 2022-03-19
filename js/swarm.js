//swarm js-tar metafile name
window.META_FILE_NAME = '.swarmgatewaymeta.json';

//swarm api getway for download files from swarm
window.swarmGateway = "https://api.gateway.ethswarm.org/bzz/";

//swarm api gateway for upload files to swarm
window.swarmGatewayList = [
  "https://gateway-proxy-bee-0-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-1-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-2-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-3-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-4-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-5-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-6-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-7-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-8-0.gateway.ethswarm.org/bzz",
  "https://gateway-proxy-bee-9-0.gateway.ethswarm.org/bzz"
];

// fetch file from swarm by hash
async function fetchReferenceFromSwarm(hash){
  var res = await fetch(window.swarmGateway+hash + "/" + window.INDEX_FILENAME, {
    "headers": {
      "accept": "application/json, text/plain, */*",
      "accept-language": "zh-CN,zh;q=0.9",
      "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"macOS\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-site"
    },
    "referrer": window.location.href,
    "referrerPolicy": "strict-origin-when-cross-origin",
    "method": "GET",
    "mode": "cors",
    "credentials": "omit"
  });

  if(res.status < 200 || res.status >= 300){
    return null;
  }

  return await res.json();
}

//upload js-tar files collection to swarm and return the file reference
//try every swarm gateway until it success, because swarm is not so stable now.

async function uploadReferenceToSwarm(data){
  for(var i = 0; i < window.swarmGatewayList.length; i++){
    try {

      var res = await fetch(window.swarmGatewayList[i], {
        "headers": {
          "accept": "application/json, text/plain, */*",
          "accept-language": "zh-CN,zh;q=0.9",
          "content-type": "application/x-tar",
          "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"",
          "sec-ch-ua-mobile": "?0",
          "sec-ch-ua-platform": "\"macOS\"",
          "sec-fetch-dest": "empty",
          "sec-fetch-mode": "cors",
          "sec-fetch-site": "same-site",
          "swarm-collection": "true",
          "swarm-index-document": "index.html",
          "swarm-postage-batch-id": "0000000000000000000000000000000000000000000000000000000000000000"
        },
        "referrer": window.location.href,
        "referrerPolicy": "strict-origin-when-cross-origin",
        "body": data,
        "method": "POST",
        "mode": "cors",
        "credentials": "omit"
      });

      if(res.status < 200 || res.status >= 300){
        return null;
      }      

      var data = await res.json();

      return data.reference;

    } catch(e){
      continue;
    }
  }

  return null;

}