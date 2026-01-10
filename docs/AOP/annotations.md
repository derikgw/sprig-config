Currently sprig-config presents a singleton Config object.

To access properties from configs, you would Config.get("some.defined.property") to get the value wether it is a straight string or object.

I had the idea of implementing meta programming where you could instead have the following:

@Config(some.defined.property)
someVar

then in the code you could:

firstName = someVar.firstName

The application.yml would contain something like:

some:
  defined:
    property:
      firstName: Luke

