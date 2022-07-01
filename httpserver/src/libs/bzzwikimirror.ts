import * as constant from '../constant'

export const getZimList = async () => {
	const url = `${constant.BZZ_WIKI_MIRROR_HOST}/api/zimlist`;

	const res = await fetch(url, {
		headers: {
			"content-type": "application/json",
		},
		"referrer": (window as any).location.href,
		"referrerPolicy": "strict-origin-when-cross-origin",
		"method": "GET",
		"mode": "cors",
		"credentials": "omit",
	});

	if (res.status < 200 || res.status > 299){
		throw new Error('get zim list failed.');
	}	

	return await res.json()
}

export const getFileList = async (pageSize:number, pageCount:number) => {
	const url = `${constant.BZZ_WIKI_MIRROR_HOST}/api/filelist/${pageSize}/${pageCount}`;

	const res = await fetch(url, {
		headers: {
			"content-type": "application/json",
		},
		"referrer": (window as any).location.href,
		"referrerPolicy": "strict-origin-when-cross-origin",
		"method": "GET",
		"mode": "cors",
		"credentials": "omit",
	});

	if (res.status < 200 || res.status > 299){
		throw new Error('get file list failed.');
	}	

	return await res.json()	
}

export const getFileSearch = async (content:string, pageSize:number, pageCount:number) => {
	const url = `${constant.BZZ_WIKI_MIRROR_HOST}/api/filesearch/${content}/${pageSize}/${pageCount}`;

	const res = await fetch(url, {
		headers: {
			"content-type": "application/json",
		},
		"referrer": (window as any).location.href,
		"referrerPolicy": "strict-origin-when-cross-origin",
		"method": "GET",
		"mode": "cors",
		"credentials": "omit",
	});

	if (res.status < 200 || res.status > 299){
		throw new Error('get file search failed.');
	}	

	return await res.json()	
}

export const getContentSearch = async (content:string, pageSize:number, pageCount:number) => {
	const url = `${constant.BZZ_WIKI_MIRROR_HOST}/api/contentsearch/${content}/${pageSize}/${pageCount}`;

	const res = await fetch(url, {
		headers: {
			"content-type": "application/json",
		},
		"referrer": (window as any).location.href,
		"referrerPolicy": "strict-origin-when-cross-origin",
		"method": "GET",
		"mode": "cors",
		"credentials": "omit",
	});

	if (res.status < 200 || res.status > 299){
		throw new Error('get content search.');
	}

	return await res.json()	
}