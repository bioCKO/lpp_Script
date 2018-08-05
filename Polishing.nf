#!/usr/bin/nextflow
params.input ="./"
params.genome ="scaff.fa"
params.Result = "Result"
Result_path = params.input+params.Result+"/"
genomeFile = file(params.genome)

Channel.fromFilePairs(params.input+'/*.R{1,2}*.fastq').into { all_reads }
process index {
    executor 'local'
    scratch true
    cpus 1 
    clusterOptions  " -d $PWD  -l nodes=1:ppn=1 -V "
    input:
		file genomeFile

    
    output:
		file "REF*" into STARgenomeIndex

    script:
    //
    // STAR Generate Index and create genome length file
    //
    """
        bwa index  ${genomeFile} -p REF

    """
}


process mapping {
    	executor 'local'
	cpus 32
	clusterOptions  " -d $PWD  -l nodes=1:ppn=16 -v PATH=$PATH"

    input:
		file STARgenome from STARgenomeIndex
		set val(sampleid),file(reads) from all_reads

    output:
		file "*.raw" into total_bam

    script:

		"""
		bwa mem  -M  -t 64  REF   ${reads[0]}  ${reads[1]}  1> ${sampleid}.sam  2>/dev/null
		
		samtools view -bS -@ 20  ${sampleid}.sam   -o  ${sampleid}.raw   2>/dev/null



"""
   
}


final_bam = total_bam.collect()
process Combine{
	publishDir "$Result_path", mode: 'move', overwrite: true
	executor 'local'
 	cpus 32
 	clusterOptions  " -d $PWD  -l nodes=1:ppn=16 -v PATH=$PATH"

        input:
                file all_bam from final_bam
        output:
		file "Polishing*" into Polishing_result
		file "Align.stats" into stats
        script:
                """
                        samtools merge -@ 32  Total.bam $all_bam
                        samtools sort  -@ 32  -m 4G Total.bam  -o Total.sort.bam
                        mv Total.sort.bam Total.bam
			bamtools stats -in Total.bam >Align.stats
			samtools index Total.bam
			Polishing.sh ${genomeFile}
                """


}






