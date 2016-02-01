URL=$1
DIR=$2
MESSAGE=$3
OUTRO=$4

mkdir -p "repos/$DIR"
cd "repos/$DIR"
git clone "$URL" .
git checkout -b update-civicjson
mv ../../new/"$DIR".json civic.json
ERROR=""
OUTPUT="$(civicjson validate)"
civicjson validate

if [ "$OUTPUT" != "civic.json file valid" ]
then
	ERROR="$( printf "
========================

There are a few errors remaining in the civic.json,
which will need a correction:

$OUTPUT

========================")"
fi

MESSAGE+="$ERROR"
MESSAGE+="$OUTRO"
git add civic.json
git commit -m "$MESSAGE" --no-verify
