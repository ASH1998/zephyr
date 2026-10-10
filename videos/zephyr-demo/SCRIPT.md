# Zephyr — continuous live demo

Voice: Jack British. One connected take; no inserted section gaps.
Audience and goal must be clear while blue/orange airflow is already moving.
All visuals are recordings of the running app. No title cards, still images,
detached diagrams or separate maths scene. Target: approximately three minutes.

## Moving airflow and who this helps (Frame 1)

    Zephyr helps vehicle designers and small engineering teams explore ways to reduce air resistance while keeping the passenger cabin unchanged. This is the car we're working on. The blue trails move around its body, and the orange trails show the wake behind it. I can rotate the view and follow the flow from the front to the rear. That's the starting point: understand the shape, ask for a change, and compare the result.

## Ask for a useful change (Frame 2)

    I'll ask Zephyr to reduce drag with a rear taper, keep the cabin fixed, and limit movement to two millimetres. NVIDIA Nemotron reads that request. Nebius Token Factory runs the model and sends its answer back to Zephyr. Here, the app has picked out the rear taper, the movement limit, and the protected cabin. I can check all three before making a change. That gives a designer a direct way to describe what they want without starting with a complicated set of controls.

## Inspect NVIDIA predictions in the app (Frame 3)

    Now I'll switch from the blue and orange illustration to NVIDIA's predicted airflow. These moving paths come from NVIDIA DoMINO, which estimates how air moves around the car. I can also switch to pressure and rotate the same shape to inspect another side. Nemotron handles the conversation through Nebius; DoMINO supplies the engineering predictions on our NVIDIA GPU. Both are part of the workflow you're seeing here, from the request to the result we can inspect.

## Reading the prediction (Frame 7)

    The pressure colours show where air pushes harder against the surface. DoMINO predicts that pressure and the friction along the body, then Zephyr adds up their effect to estimate drag. Lower drag means less force resisting the car as it moves. The model also predicts air velocity around the shape, which is what these moving paths help us inspect. This is why we're looking at both the surface and the wake: one overall number tells us whether a candidate improved, while the views help a designer understand where to investigate next.

## Open and compare a completed design (Frame 4)

    Let's open an earlier design run and put its original and changed cars side by side. This saved candidate used a larger movement allowance. The views move together, so I can compare the same part of each car from the same angle. In the change view, the highlighted areas show where the body moved, while the cabin stays fixed. I'll switch both views to pressure, then to predicted airflow. Each shape has its own calculated result, so we're comparing what changed around the car as well as the shape itself.

## Make the result clear (Frame 5)

    Here is the number we're trying to improve. Predicted drag falls from about six hundred and twenty-two newtons to six hundred and one. That's a reduction of three point three three percent. The passenger cabin hasn't moved. A designer can inspect that trade-off directly, rotate the cars, and decide which areas deserve another look. The comparison keeps the starting shape beside the candidate, so we always have a reference.

## Ask, export, continue (Frame 6)

    I can also ask what changed. NVIDIA Nemotron, served by Nebius, reads the facts from this run and explains the difference right beside the model. The answer includes the drag reduction and confirms that the cabin stayed in place. Finally, I can download the candidate geometry and its run evidence, and return to this saved comparison later. That's what Zephyr gives a small design team: a way to ask for a change, see its predicted effect, and carry the shape and the evidence into their next design decision.
