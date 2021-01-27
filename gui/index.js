(function(){
    let webSocketConnection;
    let apiRequest=function(command){
        let url="/api/"+command;
        return new Promise(function(resolve,reject){
            fetch(url)
            .then(function(r){
                return r.json();
            })
            .then(function(data){
                if (! data.status || data.status !== 'OK'){
                    reject("status: "+data.status);
                    retturn;
                }
                resolve(data);
                return;
            })
            .catch(function(error){
                reject(error);
            });
        });
    }
    let fetchList=function(){
        let listFrame=document.getElementById('mainList');
        if (! listFrame) return;
        listFrame.innerHTML='<div class="readingData blink">Reading Packages...</div>';
        apiRequest('mainEntries')
            .then(function(data){
                listFrame.innerHTML='';
                data.data.forEach(function(le){
                    let d=document.createElement('div');
                    d.classList.add('listElement');
                    let icon=document.createElement('img');
                    icon.setAttribute('src',le.icon);
                    icon.classList.add('icon');
                    d.appendChild(icon);
                    let name=document.createElement('span');
                    name.classList.add('name');
                    name.textContent=le.displayName;
                    d.appendChild(name)
                    let target=le.url;
                    d.addEventListener('click',function(){
                        window.location.href=target;
                    })
                    listFrame.appendChild(d);
                })
            })
            .catch(function(error){
                alert("unable to fetch info: "+error);
            })
    }

    window.addEventListener('load',function(){
        let title=document.getElementById('title');
        if (window.location.search.match(/title=no/)){
            if (title) title.style.display="none";
        }
        fetchList();
    })
})();