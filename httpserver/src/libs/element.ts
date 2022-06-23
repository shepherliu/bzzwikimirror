import { h } from "vue"

import { ElMessage, ElMessageBox } from 'element-plus'

//trigger an el-message
export const elMessage = async (msgtype:any, msginfo: any, useHtml = false) => {
	ElMessage({
          duration: 5000,
          showClose: true,
          dangerouslyUseHTMLString: useHtml,
          offset: 45,
          type: msgtype,
          message: useHtml ? msginfo : h('i', { style: 'color: teal' }, msginfo),
    });
}

//trigger an el-message box
export const elMessageBox = async(desc:string, title:string, options: Object, callback:Function) => {
    ElMessageBox.prompt(desc, title, options).then(({ value }) => {
        callback(value);
    });
}

export const elMessageConfirm = async(desc:string, title:string, options: Object, callback:Function) => {
    ElMessageBox.confirm(desc, title, options).then(() => {
        callback();
    });
}

//trigger an error message from metamask
export const alertMessage = async(error: any) => {
    if( error.data != undefined && 
        error.data != null && 
        error.data.message != undefined && 
        error.data.message != null){

        elMessage('error', truncateString(error.data.message, 300)); 
        return;
    }

    if( error.data != undefined && 
        error.data != null && 
        error.data.error != undefined && 
        error.data.error != null && 
        error.data.error.message != undefined && 
        error.data.error.message != null){

        elMessage('error', truncateString(error.data.error.message, 300)); 
        return;
    }    

    if( error.data != undefined && 
        error.data != null && 
        error.data.error != undefined && 
        error.data.error != null){

        elMessage('error', truncateString(error.data.error, 300)); 
        return;
    } 

    if( error.error != undefined && 
        error.error != null && 
        error.error.data != undefined &&
        error.error.data != null &&
        error.error.data.message != undefined &&
        error.error.data.message != null){

        elMessage('error', truncateString(error.error.data.message, 300)); 
        return;
    }      

    if( error.error != undefined && 
        error.error != null && 
        error.error.message != undefined &&
        error.error.message != null){

        elMessage('error', truncateString(error.error.message, 300)); 
        return;
    }           

    if( error.error != undefined &&
        error.error != null) {

        elMessage('error', truncateString(error.error, 300));
        return;   
    }

    if( error.message != undefined && 
        error.message != null){
        
        try{
            elMessage('error', truncateString(error.message, 300));    
        }catch(e){
            if( error.reason != undefined && 
                error.reason != null){
                
                try{
                    elMessage('error', truncateString(error.reason, 300));    
                }catch(e){
                    elMessage('error', truncateString(error.stack, 300));
                }
            }
        }
    }
} 

const truncateString = (src:string, len:number) => {
    if(src.length < len){
        return src;
    }

    return src.slice(0, len);
}