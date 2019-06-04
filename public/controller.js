$(function(){
	console.log('running');
	var socket = io('http://192.168.2.13:27372');

	var controlObj = {
		cars: {},
		addCar: (address)=>{
			var id = Object.keys(this.cars).length;
			cars[id] = {
				status: 'active',
				address: address
			}

			return address;
		}
	};

	//set steer power
	$('#sp').change(()=>{
		var p = $('#sp').val();
		socket.emit('sp', {val: p});
	});

	//set drive power
	$('#dp').change(()=>{
		var p = $('#dp').val();
		socket.emit('dp', {val: p});
	});

	//control car
	$('button#forward').mousedown(()=>{
		socket.emit('a1');
	}).mouseup(()=>{
		socket.emit('a0');
	});

	$(window).keydown((e)=>{
		//w
		if(e.which == 87){
			socket.emit('a1');
		}
		//a
		if(e.which == 65){
			socket.emit('tl1');
		}
		//s
		if(e.which == 83){
			socket.emit('r1');
		}
		//d
		if(e.which == 68){
			socket.emit('tr1');
		}
	}).keyup((e)=>{
		//w
		if(e.which == 87){
			socket.emit('a0');
		}
		//a
		if(e.which == 65){
			socket.emit('tl0');
		}
		//s
		if(e.which == 83){
			socket.emit('r0');
		}
		//d
		if(e.which == 68){
			socket.emit('tr0');
		}
	});

	//triggers when car is added
	socket.on('new car', (address)=>{
		console.log('creating new car controller');
		
		var id = controlObj.addCar(address);
		$('div.car-selector').append(`
			<p> Car {{ID}} <br/>
				<input type="checkbox" id="car{{ID}}"></input>
			</p>
			`).replace('{{ID}}', id); 
	});
});