// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

contract BzzWikipediaMirror {
  //owner
  address owner;

  //wiki index reference
  string  indexReference;
  // set contract owner
  constructor() {
    owner = msg.sender;
  }

  //only owner
  modifier onlyOwner() {
    if(msg.sender != owner){
      revert("this function only support for the contract owner!");
    }
    _;
  }

  event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

  function transferOwnership(address newOwner) public onlyOwner {
    require(newOwner != address(0));
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }

  //get index swarm reference
  function getIndexReference() public view returns(string memory){
    return indexReference;
  }

  //set index swarm reference
  function setIndexReference(string calldata hash) public onlyOwner returns(bool){
    if(bytes(hash).length == 0){
        revert("index reference is not given");
    }

    indexReference = hash;

    return true;
  }

  //check if contract owner or not
  function isContractOwner()public view returns(bool){
    return msg.sender == owner;
  }
 
}